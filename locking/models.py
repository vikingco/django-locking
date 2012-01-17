import datetime

from django.db import models, IntegrityError
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _

from .exceptions import NotLocked, AlreadyLocked

DEFAULT_MAX_AGE = getattr(settings, 'LOCK_MAX_AGE', 0)


def _get_lock_name(obj):
    return '%s.%s__%d' % (obj.__module__, obj.__class__.__name__, obj.id)


class LockManager(models.Manager):
    def acquire_lock(self, obj=None, max_age=DEFAULT_MAX_AGE, lock_name=''):
        '''Acquire a lock on the object'''
        if obj is not None:
            lock_name = _get_lock_name(obj)

        try:
            lock, created = self.get_or_create(locked_object=lock_name,
                                               defaults={'max_age': max_age})
        except IntegrityError:
            raise AlreadyLocked()

        if not created:
            # check whether lock is expired
            if lock.is_expired:
                lock.created_on = datetime.datetime.now()
                lock.save()
                return lock
            raise AlreadyLocked()

        return lock

    def is_locked(self, obj):
        '''Check whether a lock exists on a certain object'''
        qs = self.filter(locked_object=_get_lock_name(obj))
        return qs.count() > 0

    def get_expired_locks(self):
        '''Get all expired locks'''
        result = []
        for l in self.all():
            if l.is_expired:
                result.append(l.id)
        return self.filter(id__in=result)


class Lock(models.Model):
    locked_object = models.CharField(
        max_length=255, verbose_name=_('locked object'), unique=True
    )
    created_on = models.DateTimeField(
        auto_now_add=True, verbose_name=_('created on'), db_index=True
    )
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
        '''Release the lock'''
        if not getattr(self, 'unlocked', False):
            self.delete()
            self.unlocked = True
            return True
        if not silent:
            raise NotLocked()

    @property
    def expires_on(self):
        '''
        This ``Lock`` expires on. If ``max_age`` is 0, it will return
        ``created_on``.
        '''
        return self.created_on + datetime.timedelta(seconds=self.max_age)

    @property
    def is_expired(self):
        '''Is the ``Lock`` expired?'''
        if self.max_age == 0:
            return False
        else:
            return self.expires_on < datetime.datetime.now()
