"""
Tests for the locking application
"""
import time

from django.test import TestCase

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from .exceptions import AlreadyLocked
from .models import Lock, _get_lock_name


class LockTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='Lock test')

    def test_acquire_and_release(self):
        ''' Tests an aquire/release cycle '''
        l = Lock.objects.acquire_lock(self.user)
        self.assertTrue(Lock.objects.is_locked(self.user))
        l.release()
        self.assertTrue(not Lock.objects.is_locked(self.user))
    
    def test_obj_with_expired_lock_is_not_locked(self):
        ''' Tests that manager.is_locked returns False if locks are expired '''
        Lock.objects.acquire_lock(self.user, max_age=1)
        time.sleep(2)  # make lock expire
        self.assertFalse(Lock.objects.is_locked(self.user))

    def test_lock_twice(self):
        ''' Tests a double locking (lock and try to lock again) '''
        l = Lock.objects.acquire_lock(self.user)
        self.assertTrue(Lock.objects.is_locked(self.user))
        self.assertRaises(AlreadyLocked, Lock.objects.acquire_lock, self.user)
        self.assertTrue(Lock.objects.is_locked(self.user))
        l.release()

    def test_unlock_twice(self):
        ''' Tests a double unlocking (unlock and try to unlock again) '''
        l = Lock.objects.acquire_lock(self.user)
        self.assertTrue(Lock.objects.is_locked(self.user))
        l.release()
        self.assertTrue(not Lock.objects.is_locked(self.user))
        l.release()

    def test_model(self):
        '''Test the model'''
        l = Lock.objects.acquire_lock(self.user, max_age=10)
        self.assertTrue(l.locked_object.endswith('%d' % self.user.id))
        self.assertEquals(l.locked_object, _get_lock_name(self.user))
        self.assertTrue(l.created_on)
        self.assertEquals(l.max_age, 10)
        l.release()
        l = Lock.objects.acquire_lock(lock_name='test_lock', max_age=10)
        self.assertEquals(l.locked_object, 'test_lock')

    def test_unicode(self):
        ''' Test the __unicode__ '''
        l = Lock.objects.acquire_lock(self.user)
        str_rep = '%s' % l
        self.assertNotEquals(str_rep.find('%d' % self.user.id), -1)
        l.release()

    def test_relock(self):
        '''Test to allow lock if lock is expired'''
        l = Lock.objects.acquire_lock(self.user, max_age=1)
        time.sleep(1)
        self.assertTrue(l.is_expired)
        # try to lock again
        l2 = Lock.objects.acquire_lock(self.user, max_age=1)
        self.assertNotEquals(l.created_on, l2.created_on)

    def test_expired(self):
        '''Test the expired locks'''
        l = Lock.objects.acquire_lock(self.user, max_age=0)
        l2 = Lock.objects.acquire_lock(l, max_age=1)
        time.sleep(1)  # make lock expire
        self.assertTrue(not l.is_expired)
        self.assertTrue(l2.is_expired)
        expired_locks = Lock.objects.get_expired_locks()
        self.assertEquals(len(expired_locks), 1)
