from datetime import timedelta

from django.utils import timezone
from django.db import models, IntegrityError, transaction
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _

from .exceptions import NotLocked, AlreadyLocked, NonexistentLock, Expired


#: The default lock age.
DEFAULT_MAX_AGE = getattr(settings, 'LOCK_MAX_AGE', 0)


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
        qs = self.filter(locked_object=_get_lock_name(obj))
        return any([not lock.is_expired for lock in qs])

    def get_expired_locks(self):
        '''
        Gets all expired locks

        :returns: a :class:`~django.db.models.query.QuerySet` containing all
            expired locks
        '''
        result = []
        for l in self.all():
            if l.is_expired:
                result.append(l.id)
        return self.filter(id__in=result)


class Lock(models.Model):
    '''
    '''
    #: The lock name
    locked_object = models.CharField(
        max_length=255, verbose_name=_('locked object'), unique=True
    )
    #: The creation time of the lock
    created_on = models.DateTimeField(
        auto_now_add=True, verbose_name=_('created on'), db_index=True
    )
    #: The age of a lock before it can be overwritten. If it's ``0``, it will
    #: never expire.
    max_age = models.PositiveIntegerField(
        default=DEFAULT_MAX_AGE, verbose_name=_('Maximum lock age'),
        help_text=_('The age of a lock before it can be overwritten. '
                    '0 means indefinitely.')
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
        
        self.created_on = timezone.now()
        self.save()

    @property
    def expires_on(self):
        '''
        Gets the :class:`~datetime.datetime` this ``Lock`` expires on.

        :returns: the expiration date.  If :attr:`max_age` is ``0``, it will
            return :attr:`created_on`.
        :rtype: :class:`datetime.datetime`
        '''
        return self.created_on + timedelta(seconds=self.max_age)

    @property
    def is_expired(self):
        '''
        Is the lock expired?

        :returns: ``True`` or ``False``
        '''
        if self.max_age == 0:
            return False
        else:
            return self.expires_on < timezone.now()
