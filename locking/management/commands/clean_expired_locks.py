from locking.models import NonBlockingLock

from logging import getLogger
logger = getLogger(__name__)


try:
    from django.core.management.base import NoArgsCommand

    from optparse import make_option

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
                logger.info('Would delete %s locks' % len(locks))
            else:
                locks.delete()

except ImportError:
    # Django >= 1.10
    from django.core.management import BaseCommand


    class Command(BaseCommand):
        help = 'Remove expired locks'

        def add_arguments(self, parser):
            parser.add_argument('-n', '--dry-run', dest='dry_run', 
                        action='store_true', default=False,
                        help='Just say how many we would remove, '
                             'but don\'t actually do it')


        def handle(self, *args, **options):
            locks = NonBlockingLock.objects.get_expired_locks()
            if options['dry_run']:
                logger.info('Would delete %s locks' % len(locks))
            else:
                locks.delete()

