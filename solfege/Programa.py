#!/usr/bin/env python
#coding: utf-8
from gi.repository import Gtk, Gdk
from __future__ import absolute_import

import locale
import logging.handlers
import os
import sqlite3
import sys
import time

locale.setlocale(locale.LC_NUMERIC, "C")


import solfege
solfege.app_running = True
from solfege import application
from solfege import buildinfo
from solfege import cfg
from solfege import filesystem
from solfege import gu
from solfege import lessonfile
from solfege import optionparser
from solfege import osutils
from solfege.profilemanager import ProfileManager
from solfege import make_screenshots
from solfege import statistics
from solfege import tracebackwindow

from solfege.mainwin import MainWin, SplashWin

class Programa(Gtk.Window):    	
    
    def eventCompInte(self, widget):
    	arquivo = open("desc_exercicios/ComparacaoDeIntervalos", "r")
        self.texto = arquivo.read()
        # Altera o texto do widget "descrição"
        self.descExerc.set_text(self.texto)

    #def eventIdentInte(self, widget):
        #arquivo = open("desc_exercicios/IdentificacaoDeIntervalos.txt", "r")
        #self.texto = arquivo.read()
        #self.descExerc.set_text(self.texto

    #def eventEntoInte(self, widget):
        #arquivo = open("desc_exercicios/EntonacaoDeIntervalos.txt", "r")
        #self.texto = arquivo.read()
        #self.descExerc.set_text(self.texto)

    def __init__(self):
        Gtk.Window.__init__(self, title="Teste - 2")

        builder = Gtk.Builder()
        builder.add_from_file("Design.glade")

        window = builder.get_object("window1") 
        window.maximize()
        '''
        =====================================================================================
        Consertar o botão "Começar", que está sendo engolido pela barra inicial!
            - Intervalos  
            - Ritmo
        =====================================================================================
        '''
        # Chama o objeto do XML e ajusta o texto
        self.descExerc = builder.get_object("descExerc")
        self.descExerc.set_justify(2)

        # Chama o objeto do XML e coloca um evento
        btnCompInte = builder.get_object("btnCompInte")
        btnCompInte.connect("clicked", self.eventCompInte)

        #btnIdentInt = builder.get_object("btnIdentInt")
        #btnIdentInt.connect("clicked", self.eventIdentInt)

        #btnEntoInt = builder.get_object("btnEntoInt")
        #btnEntoInt.connect("clicked", self.eventEntoInt)

        # Destruir janela ao fechar
        window.connect("delete-event", Gtk.main_quit)
        window.show_all()	

	style_provider = Gtk.CssProvider()

	css = open('estilo.css', 'rb')
	css_data = css.read()

	style_provider.load_from_data(css_data)
	Gtk.StyleContext.add_provider_for_screen(
		Gdk.Screen.get_default(), style_provider,
		Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
	)
 
win = Programa()
#win.show_all()
Gtk.main()
