Django-locking
==============

.. image:: https://coveralls.io/repos/github/vikingco/django-db-locking/badge.svg?branch=master
    :target: https://coveralls.io/github/vikingco/django-db-locking?branch=master
.. image:: https://travis-ci.org/vikingco/django-db-locking.svg?branch=master
    :target: https://travis-ci.org/vikingco/django-db-locking

Usage
-----

Add 'locking' to your INSTALLED_APPS settings, and run migrate to initialise
create the basic table::

    python manage.py migrate


The simplest use is by using it as a context manager

::

    from locking.models import NonBlockingLock, AlreadyLocked

    with NonBlockingLock.objects.acquire_lock(obj=model_obj):
        model_obj.do_something()

Or you can keep track of the lock yourself::

    try:
        lock = NonBlockingLock.objects.acquire_lock(obj=model_obj)
    except AlreadyLocked:
        return False

    model_obj.do_something()
    lock.release()

If you have no Django model, or you want to be able to specify the lock name
yourself, you can do that too::

    # this will raise AlreadyLocked, if it's locked
    lock = NonBlockingLock.objects.acquire_lock(lock_name='my_lock')
    do_something()
    lock.release()

Note that locks can expire automatically. There is a `LOCK_MAX_AGE` settings where you can specify a default lock release value for locks in your entire Django codebase. This value can be overridden per lock by setting the `max_age` parameter.

Test
-----
You can run the tests with
::

    tox

Releases
--------
v2.0.0:
  Merging of master and pre-django-1.8 branches
  Removes management command in favor of a celery task
v1.2.1:
  Fix problem in migration to UUIDField for PostGres
v1.2.0:
  Move id to UUIDField, add code quality checks and CI
v1.1.0:
  Rename model to NonBlockingLock and add additional features
v1.0.1:
  Corrected tests and code clean-up
v1.0.0:
  Intial release.
