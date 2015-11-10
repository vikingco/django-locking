from optparse import make_option

from django.core.management.base import NoArgsCommand

from locking.models import NonBlockingLock


class Command(NoArgsCommand):
    help_text = 'Remove expired locks'
    option_list = NoArgsCommand.option_list + (
        make_option('-n', '--dry-run', action='store_true', dest='dry_run',
                    help='Just say how many we would remove, '
                         'but don\'t actually do it'),
    )

    def handle_noargs(self, **options):
        locks = NonBlockingLock.objects.get_expired_locks()
        if options['dry_run']:
            print 'Would delete %s locks' % len(locks)
        else:
            locks.delete()
