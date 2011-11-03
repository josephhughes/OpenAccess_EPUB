import xml.dom.minidom as minidom
import xml.dom
import os, os.path
import utils

class OPSContent(object):
    '''A class for instantiating content xml documents in the OPS Preferred
    Vocabulary'''
    def __init__(self, documentstring, outdirect, metadata, backdata):
        self.inputstring = documentstring
        self.doc = minidom.parse(self.inputstring)
        self.outdir = os.path.join(outdirect, 'OPS')
        self.outputs = {'Synopsis': os.path.join(outdirect, 'OPS', 'synop.xml'), 
                        'Main': os.path.join(outdirect, 'OPS', 'main.xml'), 
                        'Biblio': os.path.join(outdirect, 'OPS', 'biblio.xml'), 
                        'Tables': os.path.join(outdirect, 'OPS', 'tables.xml')}
        self.metadata = metadata
        self.backdata = backdata
        
        self.createSynopsis(self.metadata, self.backdata)
        self.createMain(self.doc)
        self.createBiblio(self.doc)
        
    def createSynopsis(self, meta, back):
        '''Create an output file containing a representation of the article 
        synopsis'''
        
        #Initiate the document, returns the document and its body element
        synop, synbody = self.initiateDocument('Synopsis file')
        
        #Create and place the title in the body element
        art_title = meta.article_meta.title
        titlenode = synop.createElement('h1')
        titlenode.childNodes = art_title.childNodes
        #for item in art_title.childNodes:
        #    titlenode.appendChild(item.cloneNode(deep = True))
        synbody.appendChild(titlenode)
        
        affiliation_index = []
        #corresp_dict = {}
        
        #Create authors
        authors = meta.article_meta.art_auths
        author_container = synop.createElement('h2')
        first = True
        #con_char = [u'*', u'\u2020', u'\u2021']
        #ccnt = 0
        for author in authors:
            if not first:
                author_container.appendChild(synop.createTextNode(', '))
            else:
                first = False
            name = author.get_name()
            affs = author.affiliation
            contact = author.contact
            author_container.appendChild(synop.createTextNode(name))
            for aff in affs:
                if aff not in affiliation_index:
                    affiliation_index.append(aff)
                sup = synop.createElement('sup')
                aref = synop.createElement('a')
                aref.setAttribute('href', u'synop.xml#{0}'.format(aff))
                aref.appendChild(synop.createTextNode(str(affiliation_index.index(aff) + 1)))
                sup.appendChild(aref)
                author_container.appendChild(sup)
            for contact in author.contact:
                sup = synop.createElement('sup')
                aref = synop.createElement('a')
                aref.setAttribute('href', u'synop.xml#{0}'.format(contact))
                #character = con_char[ccnt]
                #aref.appendChild(synop.createTextNode(character))
                aref.appendChild(synop.createTextNode('*'))
                sup.appendChild(aref)
                author_container.appendChild(sup)
                #corresp_dict[contact] = character
                #ccnt += 1
                
        synbody.appendChild(author_container)
        
        #Create a node for the affiliation text
        aff_line = synop.createElement('p')
        art_affs = meta.article_meta.art_affs
        for item in art_affs:
            if 'aff' in item.rid:
                sup = synop.createElement('sup')
                sup.setAttribute('id', item.rid)
                sup.appendChild(synop.createTextNode(str(art_affs.index(item) + 1)))
                aff_line.appendChild(sup)
                aff_line.appendChild(synop.createTextNode(item.address))
        synbody.appendChild(aff_line)
        
        #Create the Abstract
        if meta.article_meta.abstract:
            abstract = meta.article_meta.abstract
            abstitle = synop.createElement('h2')
            abstitle.appendChild(synop.createTextNode('Abstract'))
            synbody.appendChild(abstitle)
            synbody.appendChild(abstract)
            abstract.tagName = 'div'
            abstract.setAttribute('id', 'abstract')
            for title in abstract.getElementsByTagName('title'):
                title.tagName = 'h3'
            for sec in abstract.getElementsByTagName('sec'):
                sec.tagName = 'div'
            for para in abstract.getElementsByTagName('p'):
                para.tagName = 'big'
            self.italicNodeHandler(abstract)
            self.boldNodeHandler(abstract)
        
        #Create a node for the Editor
        ped = synop.createElement('p')
        ped.setAttribute('id', 'editor')
        bed = synop.createElement('b')
        editor_line = synop.createTextNode('Editor: ')
        bed.appendChild(editor_line)
        ped.appendChild(bed)
        first = True
        for editor in meta.article_meta.art_edits:
            name = editor.get_name()
            affs = editor.affiliation
            ped.appendChild(synop.createTextNode(u'{0}, '.format(name)))
            for aff in affs:
                for item in meta.article_meta.art_affs:
                    if item.rid == aff:
                        address = item.address
                        if first:
                            ped.appendChild(synop.createTextNode(u'{0}'.format(address)))
                            first = False
                        else:
                            ped.appendChild(synop.createTextNode(u'; {0}'.format(address)))
        synbody.appendChild(ped)
        
        #Create a node for the dates
        datep = synop.createElement('p')
        datep.setAttribute('id', 'dates')
        hist = meta.article_meta.history
        dates = meta.article_meta.art_dates
        datelist = [('Received', hist['received']), 
                    ('Accepted', hist['accepted']), 
                    ('Published', dates['epub'])]
        
        for _bold, _data in datelist:
            bold = synop.createElement('b')
            bold.appendChild(synop.createTextNode('{0} '.format(_bold)))
            datep.appendChild(bold)
            datestring = _data.niceString()
            datep.appendChild(synop.createTextNode('{0} '.format(datestring)))
        synbody.appendChild(datep)
        
        #Create a node for the Copyright text:
        copp = synop.createElement('p')
        copp.setAttribute('id', 'copyright')
        copybold = synop.createElement('b')
        copybold.appendChild(synop.createTextNode('Copyright: '))
        copp.appendChild(copybold)
        copystr = u'{0} {1} {2}'.format(u'\u00A9', 
                                        meta.article_meta.art_copyright_year, 
                                        meta.article_meta.art_copyright_statement)
        copp.appendChild(synop.createTextNode(copystr))
        synbody.appendChild(copp)
        
        #Create a node for the Funding text
        fundp = synop.createElement('p')
        fundp.setAttribute('id', 'funding')
        fundbold = synop.createElement('b')
        fundbold.appendChild(synop.createTextNode('Funding: '))
        fundp.appendChild(fundbold)
        fundp.appendChild(synop.createTextNode(back.funding))
        synbody.appendChild(fundp)
        
        #Create a node for the Competing Interests text
        compip = synop.createElement('p')
        compip.setAttribute('id', 'competing-interests')
        compibold = synop.createElement('b')
        compibold.appendChild(synop.createTextNode('Competing Interests: '))
        compip.appendChild(compibold)
        compip.appendChild(synop.createTextNode(back.competing_interests))
        synbody.appendChild(compip)
        
        #Create a node for the correspondence text
        corr_line = synop.createElement('p')
        art_corresps = meta.article_meta.art_corresps
        art_corr_nodes = meta.article_meta.correspondences
        
        # PLoS does not appear to list more than one correspondence... >.<
        corr_line.setAttribute('id', art_corresps[0].rid)
        corresp_text = utils.serializeText(art_corr_nodes[0])
        corr_line.appendChild(synop.createTextNode(corresp_text))
        
        #Handle conversion of ext-link to <a>
        ext_links = synop.getElementsByTagName('ext-link')
        for ext_link in ext_links:
            ext_link.tagName = u'a'
            ext_link.removeAttribute('ext-link-type')
            href = ext_link.getAttribute('xlink:href')
            ext_link.removeAttribute('xlink:href')
            ext_link.removeAttribute('xlink:type')
            ext_link.setAttribute('href', href)
        
        # If they did, this approach might be used
        #for item in art_corresps:
        #    sup = synop.createElement('sup')
        #    sup.setAttribute('id', item.rid)
        #    sup.appendChild(synop.createTextNode(corresp_dict[item.rid]))
        #    corr_line.appendChild(sup)
        #    if item.address:
        #        add = synop.createTextNode('Address: {0} '.format(item.address))
        #        corr_line.appendChild(add)
        #    if item.email:
        #        add = synop.createTextNode('E-mail: {0} '.format(item.email))
        #        corr_line.appendChild(add)
        synbody.appendChild(corr_line)
        
        self.postNodeHandling(synbody, synop)
        
        with open(self.outputs['Synopsis'],'wb') as out:
            out.write(synop.toprettyxml(encoding = 'utf-8'))

    def createMain(self, doc):
        '''Create an output file containing the main article body content'''
        #Initiate the document, returns the document and its body element
        main, mainbody = self.initiateDocument('Main file')
        
        body = doc.getElementsByTagName('body')[0]
        
        #Here we copy the entirety of the body element over to our main document
        for item in body.childNodes:
            mainbody.appendChild(item.cloneNode(deep = True))
        
        #Process figures
        self.figNodeHandler(mainbody, main) #Convert <fig> to <img>
        
        #Process tables
        tab_doc, tab_docbody = self.initiateDocument('HTML Versions of Tables')
        self.tableWrapNodeHandler(mainbody, main, tab_docbody) #Convert <table-wrap>
        self.postNodeHandling(tab_docbody, tab_doc)
        
        #General processing
        self.postNodeHandling(mainbody, main, ignorelist = [])
        #Conversion of existing <div><title/></div> to <div><h#/></div>
        self.divTitleFormat(mainbody, depth = 0) #Convert <title> to <h#>...
        
        #If any tables were in the article, make the tablss.xml
        if tab_docbody.getElementsByTagName('table'):
            with open(self.outputs['Tables'],'wb') as output:
                output.write(tab_doc.toprettyxml(encoding = 'utf-8'))
            
        
        caps = mainbody.getElementsByTagName('caption')
        for cap in caps:
            cap.tagName = u'div'
        
        #Handle the display of inline equations
        inline_equations = mainbody.getElementsByTagName('inline-formula')
        for each in inline_equations:
            parent = each.parentNode
            sibling = each.nextSibling
            
            inline_graphic = each.getElementsByTagName('inline-graphic')[0]
            xlink_href_id = inline_graphic.getAttribute('xlink:href')
            name = xlink_href_id.split('.')[-1]
            img = None
            startpath = os.getcwd()
            os.chdir(self.outdir)
            for path, _subdirs, filenames in os.walk('images'):
                for filename in filenames:
                    if os.path.splitext(filename)[0] == name:
                        img = os.path.join(path, filename)
            os.chdir(startpath)
            
            imgnode = main.createElement('img')
            imgnode.setAttribute('src', img)
            imgnode.setAttribute('alt', 'An inline formula')
            
            parent.insertBefore(imgnode, sibling)
            parent.removeChild(each)
            
        
        #Handle the display of out of line equations
        #Requires separating children to two <p> tags flanking the displayed 
        #formula
        disp_equations = mainbody.getElementsByTagName('disp-formula')
        for disp in disp_equations:
            
            parent = disp.parentNode
            sibling = disp.nextSibling
            
            if sibling:
                new_parent = main.createElement('p')
                disp_index = parent.childNodes.index(disp)
                for child in parent.childNodes[(disp_index +1):]:
                    new_parent.appendChild(child)
            else:
                new_parent = None
            
            grandparent = parent.parentNode
            parent_sib = parent.nextSibling
            if parent_sib:
                disp_p_node = main.createElement('p')
                grandparent.insertBefore(disp_p_node, parent_sib)
                if new_parent:
                    grandparent.insertBefore(new_parent, parent_sib)
            
            else:
                grandparent.appendChild(disp_p_node_)
                grandparent.appendChild(newparent)
            
            graphic = disp.getElementsByTagName('graphic')[0]
            
            xlink_href_id = graphic.getAttribute('xlink:href')
            name = xlink_href_id.split('.')[-1]
            img = None
            startpath = os.getcwd()
            os.chdir(self.outdir)
            for path, _subdirs, filenames in os.walk('images'):
                for filename in filenames:
                    if os.path.splitext(filename)[0] == name:
                        img = os.path.join(path, filename)
            os.chdir(startpath)
            
            imgnode = main.createElement('img')
            imgnode.setAttribute('src', img)
            imgnode.setAttribute('alt', 'A display formula')
            
            disp_p_node.appendChild(imgnode)
            parent.removeChild(disp)
            
        #Need to handle lists in the document
        lists = mainbody.getElementsByTagName('list')
        for list in lists:
            try:
                title = utils.getTagData(list.getElementsByTagName('title'))
                list.setAttribute('title', title)
                list.removeChild('title')
            except:
                pass
            try:
                list_id = list.getAttribute('id')
                list_content = list.getAttribute('list-content')
                list_type = list.getAttribute('list-type')
                prefix_word = list.getAttribute('prefix-word')
            except:
                pass
            
            if list_type == u'order':
                list.tagName = u'ol'
            elif list_type == u'bullet':
                list.tagName = u'ul'
            elif list_type == u'alpha-lower':
                list.tagName = u'ol'
            elif list_type == u'alpha-upper':
                list.tagName = u'ol'
            elif list_type == u'roman-lower':
                list.tagName = u'ol'
            elif list_type == u'roman-upper':
                list.tagName = u'ol'
            elif list_type == u'simple':
                list.tagName = u'ul'
                list.setAttribute('style','simple')
            else:
                list.tagName = 'ul'
                print('Unknown List Type in document!')
                prefix_word = '!' + prefix_word
            
            list_items = list.getElementsByTagName('list-item')
            for list_item in list_items:
                list_item.tagName = u'li'
            
            try:
                list.removeAttribute('list-content')
            except:
                pass
            try:
                list.removeAttribute('list-type')
            except:
                pass
            try:
                list.removeAttribute('prefix-word')
            except:
                pass
        
        #Convert supplementary-material tags to div tags
        #for now they will just be "sanitized", but in the future they
        #should try to provide valid links to the materials
        supp_mats = mainbody.getElementsByTagName('supplementary-material')
        for supp_mat in supp_mats:
            supp_id = supp_mat.getAttribute('id')
            supp_mat.tagName = u'div'
            label = supp_mat.getElementsByTagName('label')[0]
            label.tagName = u'b'
            self.boldNodeHandler(supp_mat)
            self.italicNodeHandler(supp_mat)
            try:
                supp_mat.removeAttribute('mimetype')
            except:
                pass
            try:
                supp_mat.removeAttribute('position')
            except:
                pass
            try:
                plos_jrns= {'pgen': 'http://www.plosgenetics.org/', 
                            'pone': 'http://www.plosone.org/', 
                            'pbio': 'http://www.plosbiology.org/', 
                            'pcbi': 'http://www.ploscompbiol.org/', 
                            'ppat': 'http://www.plospathogens.org/', 
                            'pmed': 'http://www.plosmedicine.org/', 
                            'pntd': 'http://www.plosntds.org/'}
                jrn = supp_id.split('.')[0]
                plos_fetch = 'article/fetchSingleRepresentation.action?uri='
                xlink = supp_mat.getAttribute('xlink:href')
                href = u'{0}{1}{2}'.format(plos_jrns[jrn], plos_fetch, xlink)
                anchor = main.createElement('a')
                anchor.setAttribute('href', href)
                supp_mat.insertBefore(anchor, label)
                anchor.appendChild(label)
                supp_mat.removeAttribute('xlink:href')
            except:
                pass
            try:
                supp_mat.removeAttribute('xlink:type')
            except:
                pass
        
        ext_links = main.getElementsByTagName('ext-link')
        for ext_link in ext_links:
            ext_link.tagName = u'a'
            ext_link.removeAttribute('ext-link-type')
            href = ext_link.getAttribute('xlink:href')
            ext_link.removeAttribute('xlink:href')
            ext_link.removeAttribute('xlink:type')
            ext_link.setAttribute('href', href)
            
        self.boldNodeHandler(mainbody)
        
        with open(self.outputs['Main'],'wb') as out:
            out.write(main.toprettyxml(encoding = 'utf-8'))
        
    def createBiblio(self, doc):
        '''Create an output file containing the article bibliography'''
        #Initiate the document, returns the document and its body element
        biblio, bibbody = self.initiateDocument('Bibliography file')
        
        back = doc.getElementsByTagName('back')[0]
        
        bib_title = doc.createElement('h2')
        bib_title.appendChild(doc.createTextNode('References'))
        bibbody.appendChild(bib_title)
        
        refs = back.getElementsByTagName('ref')
        for item in refs:
            bibbody.appendChild(self.parseRef(item, biblio))
        
        #for item in back.childNodes:
        #    if not item.nodeType == item.TEXT_NODE:
        #        if not item.tagName == u'fn-group':bold
        #            bibbody.appendChild(item.cloneNode(deep = True))
        
        #The biblio is currently entirely rendered instead of copied, as such
        #it has no need of postNodeHandling()
        
        with open(self.outputs['Biblio'],'wb') as out:
            out.write(biblio.toprettyxml(encoding = 'utf-8'))
            
    def parseRef(self, fromnode, doc):
        '''Interprets the references in the article back reference list into 
        comprehensible xml'''
        
        #Create a paragraph tag to contain the reference text data
        ref_par = doc.createElement('p')
        #Set the fragment identifier for the paragraph tag
        ref_par.setAttribute('id', fromnode.getAttribute('id'))
        #Pull the label node into a node_list
        label = fromnode.getElementsByTagName('label')
        #Collect the citation tag and its citation type
        citation = fromnode.getElementsByTagName('citation')[0]
        citation_type = citation.getAttribute('citation-type')
        
        #Format the reference string if it is a Journal citation type
        if citation_type == u'journal':
            ref_string = u''
            #Append the Label text
            ref_string += u'{0}. '.format(utils.getTagData(label))
            #Collect the author names and construct a formatted string
            auths = fromnode.getElementsByTagName('name')
            for auth in auths:
                surname = auth.getElementsByTagName('surname')
                given = auth.getElementsByTagName('given-names')
                name_str = u'{0} {1}'.format(utils.getTagData(surname),
                                             utils.getTagData(given))
                if auth.nextSibling:
                    name_str += u', '
                else:
                    name_str += u' '
                ref_string += name_str
            #Determine existence of <etal/> and append string if true
            etal = fromnode.getElementsByTagName('etal')
            if etal:
                ref_string += u'et al. '
            #Extract the year data
            year = fromnode.getElementsByTagName('year')
            ref_string += u'({0}) '.format(utils.getTagData(year))
            #Extract the article title
            art_title = fromnode.getElementsByTagName('article-title')
            ref_string += u'{0} '.format(utils.getTagData(art_title))
            #Extract the source data
            source = fromnode.getElementsByTagName('source')
            ref_string += u'{0} '.format(utils.getTagData(source))
            #Extract the volume data
            volume = fromnode.getElementsByTagName('volume')
            ref_string += u'{0}'.format(utils.getTagData(volume))
            #Issue data may be present, handle both options
            issue = fromnode.getElementsByTagName('issue')
            if issue:
                ref_string += u'({0}): '.format(utils.getTagData(issue))
            else:
                ref_string += u': '
            #Extract the fpage data
            fpage = fromnode.getElementsByTagName('fpage')
            ref_string += u'{0}'.format(utils.getTagData(fpage))
            #lpage data may be present, handle both options
            lpage = fromnode.getElementsByTagName('lpage')
            if lpage:
                ref_string += u'-{0}.'.format(utils.getTagData(lpage))
            else:
                ref_string += u'.'
            
            ref_par.appendChild(doc.createTextNode(ref_string))
        
        elif citation_type == u'other':
            ref_string = u'{0}. '.format(utils.getTagData(label))
            ref_string += self.refOther(citation, stringlist = [])
            ref_par.appendChild(doc.createTextNode(ref_string[:-2]))
            
        return ref_par
            
    def refOther(self, node, stringlist = []):
        '''Attempts to broadly handle Other citation types and produce a 
        human intelligible string output'''
        
        for item in node.childNodes:
            if item.nodeType == item.TEXT_NODE and not item.data == u'\n':
                if item.data.lstrip():
                    if item.parentNode.tagName == u'year':
                        stringlist.append(u'({0})'.format(item.data))
                        stringlist.append(u', ')
                    elif item.parentNode.tagName == u'source':
                        stringlist.append(u'[{0}]'.format(item.data))
                        stringlist.append(u', ')
                    elif item.parentNode.tagName == u'article-title':
                        stringlist.append(u'\"{0}\"'.format(item.data))
                        stringlist.append(u', ')
                    else:
                        stringlist.append(item.data)
                        stringlist.append(u', ')
            else:
                self.refOther(item, stringlist)
        return u''.join(stringlist)
    
    def postNodeHandling(self, topnode, doc, ignorelist = []):
        '''A wrapper function for all of the node handlers. Conceptually,
        this function should be called after special cases have been handled 
        such as in figures, tables, and references. This function provides 
        simple access to the entire cohort of default nodeHandlers which may 
        be utilized after special cases have been handled. Passing a list of 
        string tagNames allows those tags to be ignored'''
        handlers = {'bold': self.boldNodeHandler(topnode), 
                    'italic': self.italicNodeHandler(topnode), 
                    'underline': self.underlineNodeHandler(topnode), 
                    'xref': self.xrefNodeHandler(topnode), 
                    'sec': self.secNodeHandler(topnode), 
                    'named-content': self.namedContentNodeHandler(topnode)}
        
        for tagname in handlers:
            if tagname not in ignorelist:
                handlers[tagname]
    
    def figNodeHandler(self, topnode, doc):
        '''Handles conversion of <fig> tags under the provided topnode. Also 
        handles Nodelists by calling itself on each Node in the NodeList.'''
        try:
            fig_nodes = topnode.getElementsByTagName('fig')
        except AttributeError:
            for item in topnode:
                self.figNodeHandler(item, doc)
        else:
            for fig_node in fig_nodes:
                #These are in order
                fig_object_id = fig_node.getElementsByTagName('object-id') #zero or more
                fig_label = fig_node.getElementsByTagName('label') #zero or one
                fig_caption = fig_node.getElementsByTagName('caption') #zero or one
                #Accessibility Elements ; Any combination of
                fig_alt_text = fig_node.getElementsByTagName('alt-text')
                fig_long_desc = fig_node.getElementsByTagName('long-desc')
                #Address Linking Elements ; Any combination of
                fig_email = fig_node.getElementsByTagName('email')
                fig_ext_link = fig_node.getElementsByTagName('ext-link')
                fig_uri = fig_node.getElementsByTagName('uri')
                #Document location information
                fig_parent = fig_node.parentNode
                fig_sibling = fig_node.nextSibling
                #This should provide the fragment identifier
                fig_id = fig_node.getAttribute('id')
                
                if fig_alt_text: #Extract the alt-text if list non-empty
                    fig_alt_text_text = utils.getTagData(fig_alt_text)
                else:
                    fig_alt_text_text = 'A figure'
                    
                if fig_long_desc:
                    fig_long_desc_text = utils.getTagData(fig_long_desc)
                else:
                    fig_long_desc_text = None
                
                #In this case, we will create an <img> node to replace <fig>
                img_node = doc.createElement('img')
                
                #The following code block uses the fragment identifier to
                #locate the correct source file based on PLoS convention
                name = fig_id.split('-')[-1]
                startpath = os.getcwd()
                os.chdir(self.outdir)
                for path, _subdirs, filenames in os.walk('images'):
                    for filename in filenames:
                        if os.path.splitext(filename)[0] == name:
                            img_src = os.path.join(path, filename)
                os.chdir(startpath)
                #Now we can begin to process to output
                try:
                    img_node.setAttribute('src', img_src)
                except NameError:
                    print('Image source not found')
                    img_node.setAttribute('src', 'not_found')
                img_node.setAttribute('id', fig_id)
                img_node.setAttribute('alt', fig_alt_text_text)
                #The handling of longdesc is important to accessibility
                #Due to the current workflow, we will be storing the text of 
                #longdesc in the optional title attribute of <img>
                #A more optimal strategy would be to place it in its own text
                #file, we need to change the generation of the OPF to do this
                #See http://idpf.org/epub/20/spec/OPS_2.0.1_draft.htm#Section2.3.4
                if fig_long_desc_text:
                    img_node.setAttribute('title', fig_long_desc_text)
                
                #Replace the fig_node with img_node
                fig_parent.replaceChild(img_node, fig_node)
                
                #Handle the figure caption if it exists
                if fig_caption:
                    fig_caption_node = fig_caption[0] #Should only be one if nonzero
                    #Modify this <caption> in situ to <div class="caption">
                    fig_caption_node.tagName = u'div'
                    fig_caption_node.setAttribute('class', 'caption')
                    if fig_label: #Extract the label text if list non-empty
                        fig_label_text = utils.getTagData(fig_label)
                        #Format the text to bold and prepend to caption children
                        bold_label_text = doc.createElement('b')
                        bold_label_text.appendChild(doc.createTextNode(fig_label_text + '.'))
                        fig_caption_node.insertBefore(bold_label_text, fig_caption_node.firstChild)
                        #We want to handle the <title> in our caption/div as a special case
                        #For this reason, figNodeHandler should be called before divTitleFormat
                        for _title in fig_caption_node.getElementsByTagName('title'):
                            _title.tagName = u'b'
                    #Place after the image node
                    if fig_sibling:
                        fig_parent.insertBefore(fig_caption_node, fig_sibling)
                    else:
                        fig_parent.appendChild(fig_caption_node)
                
                #Handle email
                for email in fig_email:
                    email.tagName = 'a'
                    text = each.getTagData
                    email.setAttribute('href','mailto:{0}'.format(text))
                    if fig_sibling:
                        fig_parent.insertBefore(email, fig_sibling)
                    else:
                        fig_parent.appendChild(email)
                #ext-links are currently ignored
                
                #uris are currently ignored
                
                #Fig may contain many more elements which are currently ignored
                #See http://dtd.nlm.nih.gov/publishing/tag-library/2.0/n-un80.html
                #For more details on what could be potentially handled
                
    
    def tableWrapNodeHandler(self, topnode, doc, tabdoc):
        '''Handles conversion of <table-wrap> tags under the provided topnode. 
        Also handles NodeLists by calling itself on each Node in the NodeList. 
        Must be compliant with the Journal Publishing Tag Set 2.0 and produce 
        OPS 2.0.1 compliant output. HTML versions of tables will be exported to
        tables.xml and must be fully HTML compliant'''
        try:
            table_wraps = topnode.getElementsByTagName('table-wrap')
        except AttributeError:
            for item in topnode:
                self.tableWrapNodeHandler(item, doc)
        else:
            for tab_wrap in table_wraps:
                #These are in order
                tab_object_id = tab_wrap.getElementsByTagName('object-id') #zero or more
                tab_label = tab_wrap.getElementsByTagName('label') #zero or one
                tab_caption = tab_wrap.getElementsByTagName('caption') #zero or one
                #Accessibility Elements ; Any combination of
                tab_alt_text = tab_wrap.getElementsByTagName('alt-text')
                tab_long_desc = tab_wrap.getElementsByTagName('long-desc')
                #Address Linking Elements ; Any combination of
                tab_email = tab_wrap.getElementsByTagName('email')
                tab_ext_link = tab_wrap.getElementsByTagName('ext-link')
                tab_uri = tab_wrap.getElementsByTagName('uri')
                #Document location information
                tab_parent = tab_wrap.parentNode
                tab_sibling = tab_wrap.nextSibling
                #This should provide the fragment identifier
                tab_id = tab_wrap.getAttribute('id')
                
                if tab_alt_text: #Extract the alt-text if list non-empty
                    tab_alt_text_text = utils.getTagData(tab_alt_text)
                else:
                    tab_alt_text_text = 'A figure'
                    
                if tab_long_desc:
                    tab_long_desc_text = utils.getTagData(tab_long_desc)
                else:
                    tab_long_desc_text = None
                
                #In this case, we will create an <img> node to replace <table-wrap>
                img_node = doc.createElement('img')
                
                #The following code block uses the fragment identifier to
                #locate the correct source file based on PLoS convention
                name = tab_id.split('-')[-1]
                startpath = os.getcwd()
                os.chdir(self.outdir)
                for path, _subdirs, filenames in os.walk('images'):
                    for filename in filenames:
                        if os.path.splitext(filename)[0] == name:
                            img_src = os.path.join(path, filename)
                os.chdir(startpath)
                
                #Now we can begin to process to output
                try:
                    img_node.setAttribute('src', img_src)
                except NameError:
                    print('Image source not found')
                    img_node.setAttribute('src', 'not_found')
                img_node.setAttribute('alt', tab_alt_text_text)
                #The handling of longdesc is important to accessibility
                #Due to the current workflow, we will be storing the text of 
                #longdesc in the optional title attribute of <img>
                #A more optimal strategy would be to place it in its own text
                #file, we need to change the generation of the OPF to do this
                #See http://idpf.org/epub/20/spec/OPS_2.0.1_draft.htm#Section2.3.4
                if tab_long_desc_text:
                    img_node.setAttribute('title', tab_long_desc_text)
                
                #Replace the tab_wrap_node with img_node
                tab_parent.replaceChild(img_node, tab_wrap)
                
                #Handle the table caption if it exists
                if tab_caption:
                    tab_caption_node = tab_caption[0] #There should only be one
                    tab_caption_title = tab_caption_node.getElementsByTagName('title')
                    tab_caption_title_node = None
                    if tab_caption_title:
                        tab_caption_title_node = tab_caption_title[0]
                
                #Create a Table header, includes label and title, place before the image
                tab_header = doc.createElement('div')
                tab_header.setAttribute('class', 'table_header')
                tab_header.setAttribute('id', tab_id)
                if tab_label:
                    tab_header_b = doc.createElement('b')
                    for item in tab_label[0].childNodes:
                        tab_header_b.appendChild(item.cloneNode(deep = True))
                    tab_header_b.appendChild(doc.createTextNode(u'. '))
                    tab_header.appendChild(tab_header_b)
                if tab_caption_title_node:
                    for item in tab_caption_title_node.childNodes:
                        tab_header.appendChild(item.cloneNode(deep = True))
                tab_parent.insertBefore(tab_header, img_node)
                
                #Handle email
                for email in tab_email:
                    email.tagName = 'a'
                    text = each.getTagData
                    email.setAttribute('href','mailto:{0}'.format(text))
                    if tab_sibling:
                        tab_parent.insertBefore(email, tab_sibling)
                    else:
                        tab_parent.appendChild(email)
                
                #Handle <table>s: This is an XHTML Table Model (less the <caption>)
                #These text format tables are useful alternatives to the 
                #rasterized images in terms of accessibility and machine-
                #readability. This element should be preserved and placed in
                #tables.xml
                tables = tab_wrap.getElementsByTagName('table')
                tab_first = True
                for table in tables:
                    try:
                        table.removeAttribute('alternate-form-of')
                    except xml.dom.NotFoundErr:
                        pass
                    if tab_first:
                        table.setAttribute('id', 'h{0}'.format(name))
                    #Unfortunately, this XHTML Table Model is allowed to have
                    #unorthodox elements... the fooNodeHandler methods may be necessary
                    self.boldNodeHandler(table)
                    self.xrefNodeHandler(table)
                    self.italicNodeHandler(table)
                    
                    #Add the table to the table document
                    tabdoc.appendChild(table)
                
                #Create a link to the HTML table version
                h_link = doc.createElement('a')
                h_link.setAttribute('href', 'tables.xml#h{0}'.format(name))
                h_link.appendChild(doc.createTextNode('HTML version of this table'))
                
                
                tab_parent.insertBefore(h_link, tab_sibling)
                
                #Handle <table-wrap-foot>
                #Because the contents of this element are presented by PLoS in 
                #the rasterized image, it makes little sense to include it in 
                #the text itself, instead we will append it to tables.xml
                tab_wrap_foots = tab_wrap.getElementsByTagName('table-wrap-foot')
                for tab_foot in tab_wrap_foots:
                    foot_div = doc.createElement('div')
                    foot_div.setAttribute('class', 'footnotes')
                    for child in tab_foot.childNodes:
                        foot_div.appendChild(child.cloneNode(deep = True))
                    for fn in foot_div.getElementsByTagName('fn'):
                        fn.tagName = 'div'
                        try:
                            fn.removeAttribute('symbol')
                        except xml.dom.NotFoundErr:
                            pass
                        try:
                            fn.removeAttribute('xml:lang')
                        except xml.dom.NotFoundErr:
                            pass
                        fn_type = fn.getAttribute('fn-type')
                        try:
                            fn.removeAttribute('fn-type')
                        except xml.dom.NotFoundErr:
                            pass
                        for label in foot_div.getElementsByTagName('label'):
                            if utils.getTagText(label):
                                label.tagName = u'b'
                            else:
                                label_parent = label.parentNode
                                label_parent.removeChild(label)
                        for title in foot_div.getElementsByTagName('title'):
                            title.tagName = u'b'
                        for cps in foot_div.getElementsByTagName('copyright-statement'):
                            cps.tagName = u'p'
                        for attr in foot_div.getElementsByTagName('attrib'):
                            attr.tagName = u'p'
                        
                        self.boldNodeHandler(foot_div)
                        self.xrefNodeHandler(foot_div)
                        self.italicNodeHandler(foot_div)
                        
                        tabdoc.appendChild(foot_div)
                        
                #Place a link in the table document that directs back to the main
                m_link = doc.createElement('a')
                m_link.setAttribute('href', 'main.xml#{0}'.format(tab_id))
                m_link.appendChild(doc.createTextNode('Back to the text'))
                m_link_p = doc.createElement('p')
                m_link_p.appendChild(m_link)
                tabdoc.appendChild(m_link_p)
                #ext-links are currently ignored
                
                #uris are currently ignored
                
                #Fig may contain many more elements which are currently ignored
                #See http://dtd.nlm.nih.gov/publishing/tag-library/2.0/n-un80.html
                #For more details on what could be potentially handled
                
                
                
            
    
    def boldNodeHandler(self, topnode):
        '''Handles proper conversion of <bold> tags under the provided 
        topnode. Also handles NodeLists by calling itself on each Node in the 
        NodeList'''
        try:
            bold_nodes = topnode.getElementsByTagName('bold')
            
        except AttributeError:
            for item in topnode:
                self.boldNodeHandler(item)
        else:
            #In this case, we can just modify them in situ
            for bold_node in bold_nodes:
                bold_node.tagName = u'b'

                
    def italicNodeHandler(self, topnode):
        '''Handles proper conversion of <italic> tags under the provided 
        topnode. Also handles NodeLists by calling itself on each Node in the 
        NodeList'''
        try:
            italic_nodes = topnode.getElementsByTagName('italic')
        except AttributeError:
            for item in topnode:
                self.italicNodeHandler(item)
        else:
            #In this case, we can just modify them in situ
            for italic_node in italic_nodes:
                italic_node.tagName = u'i'
    
    def underlineNodeHandler(self, topnode):
        '''Handles proper conversion of <underline> tags under the provided 
        topnode. Also handles NodeLists by calling itself on each Node in the 
        NodeList'''
        try:
            underline_nodes = topnode.getElementsByTagName('underline')
        except AttributeError:
            for item in topnode:
                self.underlineNodeHandler(item)
        else:
            #In this case, we can just modify them in situ
            for underline_node in underline_nodes:
                underline_node.tagName = u'span'
                underline_node.setAttribute('style', 'text-decoration:underline')
    
    def namedContentNodeHandler(self, topnode):
        '''Handles the <named-content> tag. This method needs development to 
        fit PLoS practice. Handles NodeLists by calling itself on each Node in 
        the NodeList'''
        
        #The content-type attribute can be used to identify the subject or type 
        #of content that makes this word or phrase semantically special and, 
        #therefore, to be treated differently. For example, this attribute 
        #could be used to identify a drug name, company name, or product name. 
        #It could be used to define systematics terms, such as genus, family, 
        #order, or suborder. It could also be used to identify biological 
        #components, such as gene, protein, or peptide. It could be used to 
        #name body systems, such as circulatory or skeletal. Therefore, values 
        #may include information classes, semantic categories, or types of 
        #nouns such as "generic-drug-name", "genus-species", "gene", "peptide", 
        #"product", etc.
        
        try:
            namedcontent_nodes = topnode.getElementsByTagName('named-content')
        except AttributeError:
            for item in topnode:
                self.namedContentNodeHandler(item)
        else:
            #In this case, we modify them in situ
            for nc_node in namedcontent_nodes:
                nc_content_type = nc_node.getAttribute('content-type')
                try:
                    nc_node.removeAttribute('content-type')
                except xml.dom.NotFoundErr:
                    pass
                nc_id = nc_node.getAttribute('id')
                nc_xlink_actuate = nc_node.getAttribute('xlink:actuate')
                try:
                    nc_node.removeAttribute('xlink:actuate')
                except xml.dom.NotFoundErr:
                    pass
                nc_xlink_href = nc_node.getAttribute('xlink:href')
                try:
                    nc_node.removeAttribute('xlink:href')
                except xml.dom.NotFoundErr:
                    pass
                nc_xlink_role = nc_node.getAttribute('xlink:role')
                try:
                    nc_node.removeAttribute('xlink:role')
                except xml.dom.NotFoundErr:
                    pass
                nc_xlink_show = nc_node.getAttribute('xlink:show')
                try:
                    nc_node.removeAttribute('xlink:show')
                except xml.dom.NotFoundErr:
                    pass
                nc_xlink_title = nc_node.getAttribute('xlink:title')
                try:
                    nc_node.removeAttribute('xlink:title')
                except xml.dom.NotFoundErr:
                    pass
                nc_xlink_type = nc_node.getAttribute('xlink:type')
                try:
                    nc_node.removeAttribute('xlink:type')
                except xml.dom.NotFoundErr:
                    pass
                nc_xmlns_xlink = nc_node.getAttribute('xmlns:xlink')
                try:
                    nc_node.removeAttribute('xmlns:xlink')
                except xml.dom.NotFoundErr:
                    pass
                
                #Current approach: convert to <span style="content-type">
                nc_node.tagName = u'span'
                nc_node.setAttribute('style', nc_content_type)
        
    
    def secNodeHandler(self, topnode):
        '''Handles proper conversion of <sec> tags under the provided topnode.
        Also handles NodeLists by calling itself on each Node in the NodeList. 
        '''
        try:
            sec_nodes = topnode.getElementsByTagName('sec')
        except AttributeError:
            for item in topnode:
                self.secNodeHandler(item)
        else:
            #In this case, we can just modify them in situ
            for sec_node in sec_nodes:
                sec_node.tagName = u'div'
                try:
                    sec_node.removeAttribute('sec-type')
                except xml.dom.NotFoundErr:
                    pass
    
    def xrefNodeHandler(self, topnode):
        '''Handles conversion of <xref> tags. These tags are utilized for 
        internal crossreferencing.'''
        
        #We need mappings for local files to ref-type attribute values
        ref_map = {u'bibr': u'biblio.xml#', 
                   u'fig': u'main.xml#', 
                   u'supplementary-material': u'main.xml#', 
                   u'table': u'main.xml#', 
                   u'aff': u'synop.xml#', 
                   u'sec': u'main.xml#', 
                   u'table-fn': u'tables.xml#'}
        
        try:
            xref_nodes = topnode.getElementsByTagName('xref')
        except AttributeError:
            for item in topnode:
                self.xrefNodeHandler(item)
        else:
            for xref_node in xref_nodes:
                xref_node.tagName = u'a' #Convert to <a> tag
                #Handle the ref-type attribute
                ref_type = xref_node.getAttribute('ref-type')
                xref_node.removeAttribute('ref-type')
                #Handle the rid attribute
                rid = xref_node.getAttribute('rid')
                xref_node.removeAttribute('rid')
                #Set the href attribute
                href = '{0}{1}'.format(ref_map[ref_type], rid)
                xref_node.setAttribute('href', href)
                
    def divTitleFormat(self, fromnode, depth = 0):
        '''A method for converting title tags to heading format tags'''
        taglist = ['h2', 'h3', 'h4', 'h5', 'h6']
        for item in fromnode.childNodes:
            try:
                tag = item.tagName
            except AttributeError:
                pass
            else:
                if item.tagName == u'div':
                    try:
                        divtitle = item.getElementsByTagName('title')[0]
                    except IndexError:
                        pass
                    else:
                        if not divtitle.childNodes:
                            item.removeChild(divtitle)
                        else:
                            divtitle.tagName = taglist[depth]
                            depth += 1
                            self.divTitleFormat(item, depth)
                            depth -= 1

    def initiateDocument(self, titlestring):
        '''A method for conveniently initiating a new xml.DOM Document'''
        
        impl = minidom.getDOMImplementation()
        
        mytype = impl.createDocumentType('html', 
                                         '-//W3C//DTD XHTML 1.1//EN', 
                                         'http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd')
        doc = impl.createDocument(None, 'html', mytype)
        
        root = doc.lastChild #IGNORE:E1101
        root.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml')
        root.setAttribute('xml:lang', 'en-US')
        
        head = doc.createElement('head')
        root.appendChild(head)
        
        title = doc.createElement('title')
        title.appendChild(doc.createTextNode(titlestring))
        
        link = doc.createElement('link')
        link.setAttribute('rel', 'stylesheet')
        link.setAttribute('href','css/article.css')
        link.setAttribute('type', 'text/css')
        
        meta = doc.createElement('meta')
        meta.setAttribute('http-equiv', 'Content-Type')
        meta.setAttribute('content', 'application/xhtml+xml')
        
        headlist = [title, link, meta]
        for tag in headlist:
            head.appendChild(tag)
        root.appendChild(head)
        
        body = doc.createElement('body')
        root.appendChild(body)
        
        return doc, body