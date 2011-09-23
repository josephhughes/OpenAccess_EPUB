import os, os.path, zipfile, utils

def generateHierarchy(dirname):
    os.mkdir(dirname)
    os.mkdir(os.path.join(dirname, 'META-INF'))
    ops = os.path.join(dirname, 'OPS')
    os.mkdir(ops)
    css = os.path.join(ops, 'css')
    os.mkdir(css)
    #Import CSS from resources/
    with open(os.path.join(css, 'article.css'), 'wb') as dest:
        with open('./resources/text.css', 'rb') as src:
            dest.write(src.read())
    images = os.path.join(ops, 'images')
    os.mkdir(images)
    figures = os.path.join(images, 'figures')
    os.mkdir(figures)
    tables = os.path.join(images, 'tables')
    os.mkdir(tables)
    supp = os.path.join(images, 'supplementary')
    os.mkdir(supp)
    eqn = os.path.join(images, 'equations')
    os.mkdir(eqn)
    
    # Create mimetype file in root directory
    mimepath = os.path.join(dirname, 'mimetype')
    with open(mimepath, 'w') as mimetype:
        mimetype.write('application/epub+zip')
    
    # Create the container.xml file in META-INF
    meta_path = os.path.join(dirname, 'META-INF', 'container.xml')
    with open(meta_path, 'w') as container_xml:
        container_xml.write('''<?xml version="1.0" encoding="UTF-8" ?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
   <rootfiles>
      <rootfile full-path="OPS/content.opf" media-type="application/oebps-package+xml"/>
   </rootfiles>
</container>''')
    
def generateOPF(article, dirname):
    '''Creates the content.opf document from an Article instance issued as input'''
    from xml.dom.minidom import getDOMImplementation
    from utils import createDCElement
    
    #Initiate a DOMImplementation for the OPF
    impl = getDOMImplementation()
    mydoc = impl.createDocument(None, 'package', None)
    
    package = mydoc.lastChild #grab the root package node
    package.setAttribute('version', '2.0')
    
    #Set attributes for this node, including namespace declarations
    package.setAttribute('unique-identifier', 'PrimaryID')
    package.setAttribute('xmlns:opf', 'http://www.idpf.org/2007/opf')
    package.setAttribute('xmlns:dc', 'http://purl.org/dc/elements/1.1/')
    package.setAttribute('xmlns', 'http://www.idpf.org/2007/opf')
    package.setAttribute('xmlns:oebpackage', 'http://openebook.org/namespaces/oeb-package/1.0/')
    
    # Currently, the Dublin Core will only be extended by the OPF Spec
    # See http://old.idpf.org/2007/opf/OPF_2.0_final_spec.html#Section2.2
    
    #Create the metadata, manifest, spine, and guide nodes
    nodes = ['metadata', 'manifest', 'spine', 'guide']
    for node in nodes:
        package.appendChild(mydoc.createElement(node))
    metadata, manifest, spine, guide = package.childNodes
    
    #Create useful accession points to article data
    artmeta = article.front.article_meta
    jrnmeta = article.front.journal_meta
    
    for (_data, _id) in artmeta.identifiers:
            if _id == 'doi':
                metadata.appendChild(createDCElement(mydoc, 'dc:identifier', _data,
                                                     {'id': 'PrimaryID', 'opf:scheme': 'DOI'}))
    metadata.appendChild(createDCElement(mydoc, 'dc:title', artmeta.title))
    metadata.appendChild(createDCElement(mydoc, 'dc:rights', artmeta.art_copyright_statement))
    for auth in artmeta.art_auths:
        metadata.appendChild(createDCElement(mydoc, 'dc:creator', auth.get_name(), 
                                             {'opf:role': 'aut', 'opf:file-as': auth.get_fileas_name()}))
    
    for contr in artmeta.art_edits:
        metadata.appendChild(createDCElement(mydoc, 'dc:contributor', 
                                             contr.get_name(), 
                                             {'opf:role': 'edt', 'opf:file-as': contr.get_fileas_name()}))
    
    for contr in artmeta.art_other_contrib:
        metadata.appendChild(createDCElement(mydoc, 'dc:contributor', 
                                             contr.get_name(), 
                                             {'opf:file-as': contr.get_fileas_name()}))
    
    # A context-specific tag which will be ignored for now
    #metadata.appendChild(createDCElement(mydoc, 'dc:coverage', None))
    metadata.appendChild(createDCElement(mydoc, 'dc:date', artmeta.history['accepted'].dateString(), 
                                         {'opf:event': 'creation'}))
    metadata.appendChild(createDCElement(mydoc, 'dc:date', artmeta.art_dates['epub'].dateString(), 
                                         {'opf:event': 'publication'}))
    try:
        metadata.appendChild(createDCElement(mydoc, 'dc:date', artmeta.art_dates['ecorrected'].dateString(), 
                                             {'opf:event': 'modification'}))
    except KeyError:
        pass
    
    dc_desc = metadata.appendChild(createDCElement(mydoc, 'dc:description', 
                                                   utils.serializeText(artmeta.abstract), 
                                                   ))
    if artmeta.related_articles:
        for related in artmeta.related_articles:
            print('Relation found in article-metadata!')
            metadata.appendChild(createDCElement(mydoc, 'dc:relation', 'related article found'))
    #dc:source is currently deemed unnecessary
    #metadata.appendChild(createDCELement(mydoc, 'dc:source', None))
    for subject in artmeta.article_categories.subj_groups['Discipline']:
        metadata.appendChild(createDCElement(mydoc, 'dc:subject', subject))
    metadata.appendChild(createDCElement(mydoc, 'dc:format', 'application/epub+zip'))
    metadata.appendChild(createDCElement(mydoc, 'dc:type', 
                                         artmeta.article_categories.subj_groups['heading'][0]))
    metadata.appendChild(createDCElement(mydoc, 'dc:language', 'en-US'))
    
    #manifest
    
    mimetypes = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'xml': 
                 'application/xhtml+xml', 'png': 'image/png', 'css':
                 'text/css', 'ncx': 'application/x-dtbncx+xml'}
    os.chdir(dirname)
    for path, subname, filenames in os.walk('OPS'):
        path = path[4:]
        if filenames:
            for filename in filenames:
                name, ext = os.path.splitext(filename)
                ext = ext[1:]
                newitem = manifest.appendChild(mydoc.createElement('item'))
                newitem.setAttribute('id', '{0}-{1}'.format(name, ext))
                newitem.setAttribute('href', os.path.join(path, filename))
                newitem.setAttribute('media-type', mimetypes[ext])
                
    os.chdir('..')
    
    # Spine
    spine.setAttribute('toc', 'ncx')
    testref = spine.appendChild(mydoc.createElement('itemref'))
    testref.setAttribute('idref', 'g005-png')
    testref.setAttribute('linear', 'yes')
    
    contentpath = os.path.join(dirname,'OPS','content.opf')
    with open(contentpath, 'w') as output:
        output.write(mydoc.toprettyxml(encoding = 'UTF-8'))
    
def epubZip(inputdirectory, name):
    """Zips up the input file directory into an ePub file."""
    filename = '{0}.epub'.format(name)
    epub = zipfile.ZipFile(filename, 'w')
    os.chdir(inputdirectory)
    epub.write('mimetype')
    utils.recursive_zip(epub, 'META-INF')
    utils.recursive_zip(epub, 'OPS')
    epub.close()
    os.chdir('..')
