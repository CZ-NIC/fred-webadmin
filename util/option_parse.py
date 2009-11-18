from optparse import OptionParser

parser = OptionParser()

parser.add_option('--nperms', action='store_true', dest='nperms',
                  help='Prints negative permission of all forms.')
parser.add_option('--nperms_distinct', action='store_true', dest='nperms_distinct',
                  help='Prints negative permission of all forms distinct and alphabetically sorted.')
parser.add_option('--nperms_for_class', action='store', type="string", dest='nperms_for_class',
                  help='Prints negative permission of specified class.')

(options, args) = parser.parse_args()


