from datetime import timedelta

from django.utils import timezone
from django.db import models, IntegrityError, transaction
from django.db.models import Q
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .exceptions import NotLocked, AlreadyLocked, NonexistentLock, Expired


#: The default lock age.
MAX_AGE_FOREVER = 0
DEFAULT_MAX_AGE = getattr(settings, 'LOCK_MAX_AGE', MAX_AGE_FOREVER)


def _get_lock_name(obj):
    '''
    Gets a lock name for the object.

    :param django.db.models.Model obj: the object for which we want the lock

    :returns: a name for this object
    :rtype: :class:`str`
    '''
    return '%s.%s__%d' % (obj.__module__, obj.__class__.__name__, obj.id)


class LockManager(models.Manager):
    '''
    The manager for :class:`Lock`
    '''
    def acquire_lock(self, obj=None, max_age=DEFAULT_MAX_AGE, lock_name=''):
        '''
        Acquires a lock

        :param obj: the object we want to lock, this will override
            ``lock_name``.
        :type: :class:`django.db.models.Model` or ``None``
        :param int max_age: the maximum age of the lock
        :param str lock_name: the name for the lock
        '''
        if obj is not None:
            lock_name = _get_lock_name(obj)
        
        with transaction.atomic():
            try:
                lock, created = self.get_or_create(locked_object=lock_name,
                                                   defaults={'max_age': max_age})
            except IntegrityError:
                raise AlreadyLocked()
    
            if not created:
                # check whether lock is expired
                if lock.is_expired:
                    # Create a new lock to provide a new id for renewal.
                    # This ensures the owner of the previous lock doesn't
                    # remain in possession of the active lock id.
                    lock.release()
                    lock = self.create(locked_object=lock_name, max_age=max_age)
                else:
                    raise AlreadyLocked()

        return lock

    def release_lock(self, pk):
        '''
        Releases a lock
        :param int pk: the primary key for the lock to release
        '''
        
        with transaction.atomic():
            try:
                lock = self.get(pk=pk)
            except self.model.DoesNotExist:
                raise NotLocked()
            
            lock.release()
        
        return lock

    def renew_lock(self, pk):
        '''
        Renews a lock

        :param int pk: the primary key for the lock to renew
        '''
        
        with transaction.atomic():
            try:
                lock = self.get(pk=pk)
            except self.model.DoesNotExist:
                raise NonexistentLock()
            
            lock.renew()
        
        return lock

    def is_locked(self, obj):
        '''
        Check whether a lock exists on a certain object

        :param django.db.models.Model obj: the object which we want to check

        :returns: ``True`` if one exists
        '''
        return self.filter(locked_object=_get_lock_name(obj)).filter(self.not_expired_lookup).exists()

    def get_expired_locks(self):
        '''
        Gets all expired locks

        :returns: a :class:`~django.db.models.query.QuerySet` containing all
            expired locks
        '''
        return self.filter(self.expired_lookup)
    
    @property
    def not_expired_lookup(self):
        '''
        locks are not expired if max_age is forever or expires_on is in the future
        
        :returns: :class:`~from django.db.models.Q` matching all locks that are NOT expired
        '''
        return Q(max_age=MAX_AGE_FOREVER) | Q(expires_on__gt=timezone.now())
    
    @property
    def expired_lookup(self):
        '''
        negate the "not expired lookup"
        :returns: :class:`~from django.db.models.Q` matching all locks that ARE expired
        '''
        return ~self.not_expired_lookup
    

class Lock(models.Model):
    '''
    '''
    #: The lock name
    locked_object = models.CharField(
        max_length=255, verbose_name=_('locked object'), unique=True
    )
    #: The creation time of the lock
    created_on = models.DateTimeField(
        verbose_name=_('created on'), db_index=True
    )
    #: The renewal time of the lock
    renewed_on = models.DateTimeField(
        verbose_name=_('renewed on'), db_index=True
    )
    #: The expiration time of the lock
    expires_on = models.DateTimeField(
        verbose_name=_('expires on'), db_index=True
    )
    #: The age of a lock before it can be overwritten. If it's ``MAX_AGE_FOREVER``, it will
    #: never expire.
    max_age = models.PositiveIntegerField(
        default=DEFAULT_MAX_AGE, verbose_name=_('Maximum lock age'),
        help_text=_('The age of a lock before it can be overwritten. '
                    '%s means indefinitely.' % MAX_AGE_FOREVER)
    )

    objects = LockManager()

    class Meta:
        verbose_name = _('Lock')
        verbose_name_plural = _('Locks')
        ordering = ['created_on']

    def __unicode__(self):
        values = {'object': self.locked_object,
                  'creation_date': self.created_on}
        return _('Lock exists on %(object)s since %(creation_date)s') % values

    def release(self, silent=True):
        '''
        Releases the lock

        :param bool silent: if it's ``False`` it will raise an
            :class:`~locking.exceptions.NotLocked` error.
        '''
        if not getattr(self, 'unlocked', False):
            self.delete()
            self.unlocked = True
            return True
        if not silent:
            raise NotLocked()
    
    def renew(self):
        if self.is_expired:
            raise Expired()
        
        self.renewed_on = timezone.now()
        self.save()

    @property
    def is_expired(self):
        '''
        Is the lock expired?

        :returns: ``True`` or ``False``
        '''
        if self.max_age == MAX_AGE_FOREVER:
            return False
        else:
            return self.expires_on < timezone.now()


@receiver(pre_save, sender=Lock)
def lock_pre_save(sender, instance, raw, **kwargs):
    if not raw:
        now = timezone.now()
        
        if instance.created_on is None:
            instance.created_on = now
        
        if instance.renewed_on is None:
            instance.renewed_on = now
        
        instance.expires_on = instance.renewed_on + timedelta(seconds=instance.max_age)