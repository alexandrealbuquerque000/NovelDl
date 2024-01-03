
import os
from pathlib import Path
import time
import copy
from unidecode import unidecode
from tkinter import Tk, filedialog
from .preset_data import keys, values
import requests
from selenium.webdriver import Edge, EdgeOptions
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import re # Para filtrar a busca de títulos
from bs4 import BeautifulSoup # Para manipular e guardar dados obtidos do site
from flask import session


# Função para obter informações de todas as requisições feitas pelo programa
def getinfo(site, current_server, classinfo=None, extrainfo=None, firstfilter=None, secondfilter=None):


    def by_webdriver(site):
        
        options = EdgeOptions()
        options.headless = True
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = Edge(service=Service(EdgeChromiumDriverManager(log_level=0, print_first_line=False).install()), options = options)
        driver.get(site)
        time.sleep(1)
        
        return driver
      

    # Função para ajustar URL caso incompleta
    def thirdfilter(url):
        if url!=None and url!='':
            if url.startswith('/'):
                url=current_server.Config['basesite']+url.lstrip('/')

            return url

        return 0


    # Função para verificar a utilização de um comando
    def verifstep(step):
        if step!=None:
            if step=='None':
                step=None
            
            return step

        return 0


    # Função para definir o tipo de informação que será extraída da URL
    def get(infofilter):
        nonlocal info

        if infofilter=='text':
            exactinfo=info.get_text()
        else:
            exactinfo=info.get(infofilter)
        if exactinfo==None:
            exactinfo=''

        return exactinfo.strip()

    site=thirdfilter(site)
    headers={'User-agent': 'Mozilla/5.0'}
    rqsttime=0
    while True:
        time.sleep(rqsttime)
        try:
            response = requests.get(site, stream=True, headers=headers)
            if classinfo=='capsnamesandidsclass':
                page_text=by_webdriver(site).page_source
            else:
                page_text=response.text

        except requests.RequestException as error: 
            session['Error']=1
            print('\nOcorreu um erro: '+ str(error))
            time.sleep(1.25)

            return -10
        if response.status_code==200:
            firstfilter=verifstep(current_server.Config[firstfilter])
            secondfilter=verifstep(current_server.Config[secondfilter])
            verifclassname=classinfo
            classinfo=verifstep(current_server.Config[classinfo])
            extrainfo=verifstep(current_server.Config[extrainfo])
            soup = BeautifulSoup(page_text, 'html.parser')
            if firstfilter!=0:
                soup=soup.find(class_=firstfilter)
            if classinfo!=0 and extrainfo!=0:
                allinfo=soup.find_all(extrainfo, class_=classinfo)
            else:
                if classinfo!=0:
                    allinfo=soup.find_all(class_=classinfo)
                else:
                    allinfo=soup.find_all(extrainfo)
            listinfo=[]
            if verifclassname=='pagescapclass':

                return allinfo
            
            for info in allinfo:
                if secondfilter!=0:
                    info=info.find(secondfilter)
                if info!=None:
                    if verifclassname=='titlesandlinksclass':
                        titlesgturl=thirdfilter(get(current_server.Config['titlesgturl']))
                        if titlesgturl!=0:
                            titlesgtname=get(current_server.Config['titlesgtname'])
                            titlesgtname=titlesgtname.rstrip('.')
                            titlesgtname=re.sub(r'[:*?"><|/\\]', ' ', titlesgtname).strip()
                            listinfo.append({'Name': titlesgtname, 'URL': titlesgturl})
                    elif verifclassname=='capsnamesandidsclass':
                        capsgturl=thirdfilter(get(current_server.Config['capsgturl']))
                        capsgtname=get(current_server.Config['capsgtname'])
                        if current_server.Name=='Nexo Scans':
                            cutword='cap-'
                        if current_server.Name=='Central Novel':
                            cutword='capitulo-'
                        capsgtname = ".".join([capnum for capnum in capsgturl.split(cutword)[-1].strip('/').split('-') if capnum.isdigit()][:2])
                        capsgtname=capsgtname.rstrip('.')
                        capsgtname=re.sub(r'[:*?"><|/\\]', ' ', capsgtname).strip()
                        if len(capsgtname)!=0 and capsgturl!=0:
                            capsgtname="Capítulo {}".format(capsgtname)
                            listinfo.append({'Name': capsgtname, 'URL': capsgturl})
                    elif verifclassname=='descriptionclass':
                        description=get(current_server.Config['descriptiontxt'])
                        if type(description)==list:
                            description=description[0]
                        listinfo.append({'Description': description.strip('\n')})
                    elif verifclassname=='numtitlepgsclass':
                        listinfo.append(get(current_server.Config['titlepgsgtnum']))
                    elif verifclassname=='numcappgsclass':
                        listinfo.append(get(current_server.Config['cappgsgtnum']))
                    else:
                        listinfo.append([get('text')])
            print(listinfo)
            response.close()
            return listinfo

        else:
            if rqsttime<=3:
                rqsttime+=1
                continue

            return -100
  

 # Função para obter determinadas informações de todo o site
def getallinfolinks(Table, Ower_Table, pginf1):

    Table_Name=Table.__tablename__
    current_server=Ower_Table
    if Ower_Table == None:
        ContentList=[]
        for Name in values.items():
            Config=dict(zip(keys, Name[1]))
            Added_Content=add_data(Table, None, [{'Name': Name[0], 'Config':Config}])
            ContentList.extend(Added_Content)
        DelDescendants(Table, ContentList)
    else:
        while True:
            if current_server.__tablename__!='servers':
                current_server=current_server.Ower
            else:
                if Table_Name=='titles':
                    site_keys=('titlesandlinksclass', 'titlesextrainfo', 'firsttitlesfilter', 'secondtitlesfilter')
                elif Table_Name=='contents':
                    site_keys=('capsnamesandidsclass', 'capsextrainfo', 'firstcapfilter', 'secondcapfilter')
                else:
                    site_keys=('pagescapclass', 'cappagesextrainfo', 'firstpgscapfilter', 'secondpgscapfilter')
                pginf6, pginf7, pginf8, pginf9=site_keys
                break
        allinfolist=[]
        verifnumwebpages=None
        lastpage=0
        while True:
            lastpage+=1
            site=pginf1.format(lastpage)
            if Table_Name=='contents':
                description=getinfo(site, current_server, 'descriptionclass', 'descriptionextrainfo', 'firstdescriptionfilter', 'seconddescriptionfilter')
                if description!=-10:
                    Update(Ower_Table, description[0])
            numwebpagestest1=getinfo(site, current_server, pginf6, pginf7, pginf8, pginf9)
            if numwebpagestest1==-10:
            
                return -10
            if Table_Name=='titles':
                if numwebpagestest1==-100 or len(numwebpagestest1)==0 or numwebpagestest1==verifnumwebpages:
                    if current_server.Name=='Kissmanga' and numwebpagestest1==-100:
                        continue
                    break
                verifnumwebpages=copy.deepcopy(numwebpagestest1)
            if Table_Name=='subcontents':
                if Ower_Table.Name in [info.get_text() for info in numwebpagestest1]:
                    a=[info.get_text() for info in numwebpagestest1].index(Ower_Table.Name)+1
                    numwebpagestest1=numwebpagestest1[a:]
                html_info = [str(info) for info in numwebpagestest1]
               
                return html_info
            Added_Content=add_data(Table, Ower_Table.id, numwebpagestest1)
            allinfolist.extend(Added_Content)
            if Table_Name!='titles':
                break
        DelDescendants(Table, allinfolist, {'Ower_id': Ower_Table.id})
    

def Update(Table_Query, New_Content):
    from . import db
    
    Table=Table_Query.__table__
    Query_Dict=Table_Query.__dict__
    update_dict={}
    
    for key, value in New_Content.items():
        if Query_Dict.get(key)!=value:
            update_dict.update({key: value})
    if len(update_dict)!=0:
        db.session.execute(db.update(Table).where(Table.c.id==Table_Query.id).values(**update_dict))
        db.session.commit() 


def Get_ExactTable(Table, filters={}, order_by=None):

    return Table.query.order_by(order_by).filter_by(**filters)


def GetRefList(Table):
    RefList=[]
    for Ref in Table:
        try:
            Backref=Ref.Backref
        except AttributeError:
            pass
        else:
            if Backref.count()!=0:
                RefList.append(Backref)
    return RefList


def DelDescendants(Table, save_list, filters={}):
    from . import db

    Del_Table=Get_ExactTable(Table, filters).filter(~(Table.id.in_(save_list)))
    DelList=[Del_Table]
    TempRef=GetRefList(Del_Table)
    while True:
        DelList.extend(TempRef)
        VerifRefList=[]
        for RefElem in TempRef:
            RefList=GetRefList(RefElem)
            if len(RefList)!=0:
                VerifRefList.extend(RefList)
        if len(VerifRefList)==0:
            break
        TempRef=VerifRefList.copy()
    DelList.reverse()
    for ItemToDel in DelList:
        for ElemToDel in ItemToDel:
            db.session.delete(ElemToDel)
            db.session.commit()

def add_data(Table, Ower_id, ContentList):

    from . import db
    
    Table_Name=Table.__tablename__
    Added_Content=[]
    for dbcontent in ContentList:
        if Table_Name=='users':
            queryinfo=Table.query.filter((Table.Name==dbcontent['Name']) & (Table.Password==dbcontent['Password']))
        elif Table_Name=='servers':
            queryinfo=Table.query.filter((Table.Name==dbcontent['Name']))
        else:
            queryinfo=Table.query.filter(((Table.Name==dbcontent['Name']) | (Table.URL==dbcontent['URL'])) & (Table.Ower_id==Ower_id))
        if len(queryinfo.all())==0:
            if Ower_id!=None:
                dbcontent.update({'Ower_id': Ower_id})
            db.session.execute(db.insert(Table).values(**dbcontent))
            db.session.commit()
            queryinfo=queryinfo.first()
        else:
            queryinfo=queryinfo.first()
            Update(queryinfo, dbcontent)

        Added_Content.append(queryinfo.id)

    return Added_Content


 # Função para verificar existência de pasta ou arquivo
def verifpath(dirp, mode):

    if (os.path.exists(dirp))==True:
        if mode==0:

            return True
    else:
        if mode==0:

            return False
        else:
            os.mkdir(dirp)
        
    return dirp

# Função para obter o diretório central de destino dos arquivos
def gethqpath():

    root = Tk()
    root.geometry('0x0')
    hqpathchoose=('Selecione o diretório da pasta que deseja guardar todos os conteúdos escolhidos: ')
    hqpathstr=hqpathchoose.replace('Selecione', '\nDigite')
    print('\n'+hqpathchoose)
    hqpath = filedialog.askdirectory(parent=root, initialdir="/",title =hqpathchoose)
    root.destroy()       

    if hqpath=='':
        print('\nOpção cancelada.\n\nTente novamente')
        hqpath=input(hqpathstr)
    while ((Path(hqpath)).is_dir())==False:
        print("\nEsse diretório não existe.\n\nTente novamente.")
        hqpath=input(hqpathstr)
    
    return hqpath


# Função para carregar continuamente os dados que serão utilizados 
def downloader(contents, dir):
    from .models import Subcontents

    for Table in contents:
        title_table=Table.Ower
        title_dir=verifpath(os.path.join(verifpath(os.path.join(dir, "Novels"), 1), title_table.Name), 1)
        if any(file for file in os.listdir(title_dir) if file.endswith('.html') and os.path.splitext(file)[0]==Table.Name):

            continue

        if not session.get('Downloads'):
            session['Downloads']={}
        session['Downloads'].update({Table.Name:True})
        content_dir=os.path.join(title_dir, '{}.html'.format(Table.Name))
        print('\nBaixando: {}'.format(Table.Name))   
        html_info=getallinfolinks(Subcontents, Table, Table.URL)
        with open(content_dir, 'w', encoding="utf-8") as file:
            file.writelines(['<h2 align="center">{}</h2>'.format(Table.Name)]+html_info)
            file.close()
        print(content_dir, end='\n')
        session['Downloads'].update({Table.Name:False})
    print("\nDownloads finalizados!")