from __future__ import print_function
#! /usr/bin/env python
# coding: utf-8
# vim:ts=4:sw=4:expandtab
import random
import os
import sys
import modules.ext
import markup
sys.path.append('pyAPI.zip')

class QA_Markup(object):

    def generate_content(self,filename="",randrange=200,junk_len_min=5,junk_len_max=100):

        filename = filename
        randrange = randrange
        junk_len_min = junk_len_min
        junk_len_max = junk_len_max
        items = ()
        paras = ()
        images = ()
        styles = ()
        titles = ()
        universities = ()
        paragraphs = ()
        dates = ()
        names = ()
        positions = ()
        locations = ()
        css = ()
        junk_len = random.randrange(5,15)

        content_list = ['list', 'list+img+stylesheet', 'stylesheet+click', 'xml']
        content_index = [0,1,2,3]

        index = random.randrange(len(content_index))

        if content_list[index] == 'list':
        
            for x in range(0,random.randrange(1,randrange)):

                items = items + ("Item"+(("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8)),)

            paras = ("List Test")
            page = markup.page()

            page.init( title=(("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8)), header = (("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8)), footer = (("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8)))

            page.ul( class_='mylist')
            page.li( items, class_='myitem')
            page.ul.close()

            page.p(paras)
       
            FILE = open(filename,'w') 
            print(page, file = FILE)
            FILE.close()

        elif content_list[index] == 'list+img+stylesheet':

            for x in range(0,random.randrange(1,randrange)):

                items = items + ("Item"+(("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8)),)

            paras = ("List Test")


            for x in range(0,random.randrange(1,randrange)):

                images = images + ((("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8))+".jpg",)
                css = css + ((("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8))+".css",)

            page = markup.page()

            page.init( title=(("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8)), css=css, header = (("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8)), footer = (("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8)))

            page.ul( class_='mylist')
            page.li( items, class_='myitem')
            page.ul.close()

            page.p(paras)
            page.img(src=images, width=100, height=80, alt="Thumbnails")
            
            FILE = open(filename,'w') 
            print(page, file = FILE)
            FILE.close()
            
        elif content_list[index] == 'stylesheet+click':

            title = "Incorporation"
            header = "Header Information"
            footer = "This is the end"            

            for x in range(0,random.randrange(1,randrange)):
                styles = styles + ((("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8))+".css",)

            page = markup.page()

            page.init( css=styles, title=title, header = header, footer = footer)
            page.br()
            
            for x in range(0,random.randrange(1,randrange)):

                paragraphs = paragraphs + ((("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8)),)

            page.p(paragraphs)
            page.a( "Click this.", class_='internal', href='index.html')
            page.img( width=60, height=80, alt='Test', src=(("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8))+".css")

            FILE = open(filename,'w') 
            print(page, file = FILE)
            FILE.close()            

        elif content_list[index] == 'xml':

            for x in range(0,random.randrange(1,randrange)):
                titles = titles + ((("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8)),)
                universities = universities + ((("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8)),)
                dates = dates + ((("%%0%dX" % junk_len) % random.getrandbits(junk_len * 8)),)

                myxml = markup.page(mode = 'xml')
                myxml.init( encoding='ISO-8859-2')
                myxml.cv.open()
                myxml.talk(titles, university=universities,date=dates)
                myxml.cv.close()
                
                FILE = open(filename,'w') 
                print(myxml, file = FILE)
                FILE.close()

def main():

    markup = QA_Markup()
    markup.generate_content("test")



if __name__ == "__main__":
    main()
