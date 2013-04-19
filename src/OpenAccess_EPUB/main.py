#! /usr/bin/python

"""
This is the main execution file for OpenAccess_EPUB. It provides the primary
mode of execution and interaction.
"""

#If you change the version here, make sure to also change it in setup.py and
#the module __init__.py
__version__ = '0.2.8'

#Standard Library Modules
import argparse
import sys
import os.path
import shutil
import logging

#OpenAccess_EPUB Modules
import utils.input
from .utils.images import get_images
import opf
import ncx
import ops
from .settings import *


log = logging.getLogger('Main')


def OAEParser():
    """
    This function returns the parser args to the main method.
    """
    parser = argparse.ArgumentParser(description='OpenAccess_EPUB Parser')
    parser.add_argument('--version', action='version',
                        version='OpenAccess_EPUB {0}'.format(__version__))
    parser.add_argument('-o', '--output', action='store',
                        default=DEFAULT_OUTPUT,
                        help='Use to specify a desired output directory')
    parser.add_argument('-l', '--log-to', action='store',
                        default=DEFAULT_LOG,
                        help='Use to specify a non-default log directory')
    parser.add_argument('-I', '--images', action='store',
                        default=None,
                        help='''Specify a path to the directory containing the
                        images. This overrides the program's attempts to get
                        the images from the default directory, the image cache,
                        or the internet.''')
    parser.add_argument('-c', '--clean', action='store_true', default=False,
                        help='''Use to toggle on cleanup. With this flag,
                                the pre-zipped output will be removed.''')
    parser.add_argument('-N', '--no-epubcheck', action='store_false',
                        default=EPUBCHECK,
                        help='''Use this tag to turn off epub validation with
                        epubcheck.''')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('-i', '--input', action='store', default=False,
                       help='''Input may be a path to a local directory, a
                              URL to a PLoS journal article, or a PLoS DOI
                              string''')
    modes.add_argument('-z', '--zip', action='store', default=False,
                       help='''Input mode supporting Frontiers production from
                               zipfiles. Use the name of either of the zipfiles
                               with this mode, both zipfiles are required to be
                               in the same directory.''')
    modes.add_argument('-b', '--batch', action='store', default=False,
                       help='''Use to specify a batch directory; each
                               article inside will be processed.''')
    #modes.add_argument('-C', '--collection', action='store', default=False,
    #                   help='''Use to create an ePub file containing \
    #                           multiple resources.''')
    modes.add_argument('-cI', '--clear-image-cache', action='store_true',
                       default=False, help='''Clears the image cache''')
    modes.add_argument('-cX', '--clear-xml-cache', action='store_true',
                       default=False, help='''Clears the xml cache''')
    modes.add_argument('-cC', '--clear-cache', action='store_true',
                       default=False, help='''Clears the entire cache''')
    return parser.parse_args()


def dir_exists(outdirect):
    """
    Provides interaction with the user if the output directory already exists.
    If running in batch mode, this interaction is ignored and the directory
    is automatically deleted.
    """
    print(u'The directory {0} already exists.'.format(outdirect))
    r = raw_input('Replace? [Y/n]')
    if r in ['y', 'Y', '']:
        shutil.rmtree(outdirect)
    else:
        sys.exit('Aborting process!')


def single_input(args):
    """
    Single Input Mode works to convert a single input XML file into EPUB.

    This is probably the most typical use case and is the most highly
    configurable, see the argument parser and oaepub --help
    """
    #Determination of input type and processing
    #Input can be a path to a local XML file, a URL string, or a DOI string
    #In the case of the latter two, the XML file must be fetched
    if args.input:
        if 'http://www' in args.input:
            parsed_article, raw_name = utils.input.url_input(args.input)
        elif args.input[:4] == 'doi:':
            parsed_article, raw_name = utils.input.doi_input(args.input)
        else:
            parsed_article, raw_name = utils.input.local_input(args.input)

    #Generate the output path name, this will be the directory name for the
    #output. This output directory will later be zipped into an EPUB
    output_name = os.path.join(args.output, raw_name)

    #Make the EPUB
    make_epub(parsed_article,
              output_name,
              args.images,   # Path specifying where to find the images
              batch=False)

    #Cleanup removes the produced output directory, keeps the ePub file
    if args.clean:  # Defaults to False, --clean or -c to toggle on
        shutil.rmtree(output_name)

    #Running epubcheck on the output verifies the validity of the ePub,
    #requires a local installation of java and epubcheck.
    if args.no_epubcheck:
        epubcheck('{0}.epub'.format(output_name))


def batch_input(args):
    """
    Batch Input Mode works to convert all of the article XML files in a
    specified directory into individual article EPUB files.

    Batch Input Mode is employed under a few simplifying assumptions: any
    pre-existing folder for article EPUB conversion will be eliminated without
    asking user permission, all output that except the .epub and .log files
    will be removed, and image files in a custom directory are not being used.

    Unlike the other input modes, Batch Input Mode output is always relative to
    the batch directory rather than the working directory of oaepub execution.

    Batch Input Mode has default epubcheck behavior, it will place a system
    call to epubcheck unless specified otherwise (--no-epubcheck or -N flags).
    """
    #Iterate over all listed files in the batch directory
    for item in os.listdir(args.batch):
        item_path = os.path.join(args.batch, item)
        #Skip directories and files without .xml extension
        _root, extension = os.path.splitext(item)
        if not os.path.isfile(item_path):
            continue
        if not extension == '.xml':
            continue
        print(item_path)

        #Parse the article
        parsed_article, raw_name = utils.input.local_input(item_path)

        #Create the output name
        output_name = os.path.join(args.batch, raw_name)

        #Make the EPUB
        make_epub(parsed_article,
                  output_name,
                  None,  # Does not use custom image path
                  batch=True)

        #Cleanup output directory, keeps EPUB and log
        shutil.rmtree(output_name)

        #Running epubcheck on the output verifies the validity of the ePub,
        #requires a local installation of java and epubcheck.
        #if args.no_epubcheck:
            #epubcheck('{0}.epub'.format(output_name))


def collection_input(args):
    """
    Collection Input Mode is intended for the combination of multiple articles
    into a single ePub file. This may be useful for producing "Volumes", custom
    reading lists for classroom use, and compendia on common subjects.

    There is a lot of potential for how this might be used, development will
    proceed in the direction of interest.
    """
    pass


def zipped_input(args):
    """
    Zipped Input Mode is primarily intended as a workflow for Frontiers
    articles, where the article xml and relevant images are zipped together.
    """
    pass


def make_epub(document, outdirect, images, batch):
    """
    Encapsulates the primary processing work-flow. Before this method is
    called, pre-processing has occurred to define important directory and file
    locations. The document has been processed for metadata and now it is time
    to generate the ePub content.
    """
    print(u'Processing output to {0}.epub'.format(outdirect))

    #Copy files from base_epub to the new output
    if os.path.isdir(outdirect):
        if batch:
            shutil.rmtree(outdirect)
        else:
            dir_exists(outdirect)
    shutil.copytree(BASE_EPUB, outdirect)

    if document.metadata.dtdVersion() == '2.0':
        return

    #Get the Digital Object Identifier
    DOI = document.getDOI()

    #Get the images
    get_images(DOI, outdirect, images, DEFAULT_IMAGES, CACHE_IMAGES, CACHING,
               document)

    #Run content processing per publisher
    if DOI.split('/')[0] == '10.1371':  # PLoS's publisher DOI
        ops.OPSPLoS(document, outdirect)
        #TODO: Workflow change, parse table of contents from OPS processed document
        toc = ncx.TocNCX(__version__)
        toc.parseArticle(document)
        toc.write(outdirect)
        myopf = opf.PLoSOPF(__version__, outdirect, False)
    elif DOI.split('/')[0] == '10.3389':  # Frontiers' publisher DOI
        ops.OPSFrontiers(document, outdirect)
        toc = ncx.TocNCX(__version__)
        toc.parseArticle(document)
        toc.write(outdirect)
        myopf = opf.FrontiersOPF(__version__, outdirect, False)
    myopf.parse_article(document)
    myopf.write()
    utils.epubZip(outdirect)


def epubcheck(epubname):
    """
    This method takes the name of an epub file as an argument. This name is
    the input for the java execution of a locally installed epubcheck-.jar. The
    location of this .jar file is configured in settings.py.
    """
    r, e = os.path.splitext(epubname)
    if not e:
        print('Warning: Filename extension is empty, appending \'.epub\'...')
        e = '.epub'
        epubname = r + e
    elif not e == '.epub':
        print('Warning: Filename extension is not \'.epub\', appending it...')
        epubname += '.epub'
    os.execlp('java', 'OpenAccess_EPUB', '-jar', EPUBCHECK, epubname)


def main(args):
    """
    This is the main code execution block.
    """
    #Certain locations are defined by the user or by default for production
    #Here we make them if they don't already exist
    if not os.path.isdir(args.log_to):
        os.mkdir(args.log_to)
    if not os.path.isdir(args.output):
        os.mkdir(args.output)

    #The cache is a static directory which can hold various items
    #Image caching is important for some users.
    if not os.path.isdir(CACHE_LOCATION):
        utils.buildCache(CACHE_LOCATION)
    if not os.path.isdir(CACHE_LOG):
        os.mkdir(CACHE_LOG)
    if not os.path.isdir(CACHE_IMAGES):
        utils.images.init_image_cache(CACHE_IMAGES)
    if not os.path.isdir(BASE_EPUB):
        utils.makeEPUBBase(BASE_EPUB)

    #Make appropriate calls depending on input type
    #These are all mutually exclusive arguments in the argument parser
    if args.input:  # Convert single article to EPUB
        single_input(args)
    elif args.batch:  # Convert large numbers of XML files to EPUB
        batch_input(args)
    elif args.collection:  # Convert multiple XML articles into single EPUB
        collection_input(args)
    elif args.zipped:  # Convert Frontiers zipfile into single EPUB
        zipped_input(args)
