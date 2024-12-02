import os, sys, idna, pymysql, sqlalchemy, logging, re, collections, gc, time
from tkinter import *
from tkinter import filedialog, messagebox
import pandas as pd
import numpy as np
from openpyxl import load_workbook
from datetime import date, datetime, timedelta
from dateutil.rrule import rrule, DAILY, WEEKLY
from tkcalendar import DateEntry
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from matplotlib.dates import DateFormatter
import tkinter.ttk as ttk
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Flowable, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfFileMerger
from docxtpl import DocxTemplate
from jinja2 import Environment, FileSystemLoader

from io import BytesIO
from pdfrw import PdfReader, PdfDict
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl

from pandas.plotting import register_matplotlib_converters
from matplotlib import rc


class Plot_Page(Frame):

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.configure(background=back_color)

        label = Label(self, font=('arial', 30, 'bold'), text="Tie Line Comparision Plot Visualization\n(SEM vs SCADA)",
                      bd=21, bg=back_color, fg=font_color, justify=CENTER)
        label.pack(pady=10, padx=10)

        load = Image.open("inputs/img/POSOCO_Logo_transparant.png")
        render = ImageTk.PhotoImage(load)
        button_home = Button(self, image=render, width=103, height=106, bd=0, bg=back_color,
                             command=lambda: controller.show_frame(StartPage))
        button_home.image = render
        button_home.pack(side=TOP)
        button_home.place(x=0, y=0)
        # ===================== Option menu stuff ======================================================================
        self.variable = StringVar()  # to the option menu
        self.variable.set('-- Please select the Tie line --')
        self.variable.trace("w", self.callback)

        self.opt = OptionMenu(self, self.variable, *options)
        self.opt.config(width=40, font=('Helvetica', 12), bg='gray67')
        self.opt.pack(side='top')
        self.menu = self.opt["menu"]

        tree_frame = Frame(self)
        self.tree = ttk.Treeview(tree_frame, style="Custom.Treeview")
        self.tree.pack(side=LEFT, expand=YES, fill=Y)
        self.tree.tag_configure('odd', background='#4e4341')
        self.tree.tag_configure('even', background='#003551')
        self.tree.configure()

        scroll = Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill="y")

        self.tree["columns"] = ("one", "two", "three")
        self.tree.column("#0", width=370, minwidth=370)
        self.tree.column("one", width=100, minwidth=100)
        self.tree.column("two", width=100, minwidth=100)
        self.tree.column("three", width=100, minwidth=100)
        self.tree.heading("#0", text="Line Name")
        self.tree.heading("one", text="%ge Error")
        self.tree.heading("two", text="SEM MU")
        self.tree.heading("three", text="SCADA MU")


        self.tree.insert("", 0, "PG_ER1", text="PG-ER1")
        self.tree.insert("", 1, "PG_ER2", text="PG-ER2")
        self.tree.insert("", 2, "PG_odisha_project", text="PG Odisha Project")
        self.tree.insert("", 3, "WB", text="West Bengal")
        self.tree.insert("", 4, "BH", text="Bihar")
        self.tree.insert("", 5, "JH", text="Jharkhand")
        self.tree.insert("", 6, "DV", text="DVC")
        self.tree.insert("", 7, "GR", text="Odisha")
        self.tree.insert("", 8, "SI", text="Sikkim")
        self.tree.insert("", 9, "IMP_FAR_END", text="Important FAR End")
        self.tree.insert("", 10, "MIS_CALC_TO", text="MIS CALC TO End")
        self.tree.insert("", 11, "MIS_CALC_FAR", text="MIS CALC FAR End")

        self.tree.bind("<Double-1>", self.OnDoubleClick)
        tree_frame.pack(side=TOP, pady=35)
        # ======================== Latter generating buttons ====================================
        pdfReportFrame = LabelFrame(self, text='Generate letters', font=('arial', 16, 'roman'),
                                    fg='green', relief='ridge',
                                    bg=frame_bg_color, bd=20)
        pdfReportFrame.pack(side=TOP)

        btn_pdf_letters = Button(pdfReportFrame, text='PDF Letters', font=('arial', 10, 'bold'),
                            bd=5, padx=0, pady=0, bg=btn_bg_color, fg=btn_font_color, height=1, width=18,
                            command=lambda:[f() for f in [self.letter_PG_ER1, self.letter_PG_ER2,self.letter_PG_ER3, self.letter_dvc, self.letter_odisha, self.letter_sikkim, self.letter_westbengal,self.letter_bihar, self.letter_jharkhand]])
        btn_pdf_letters.grid(row=0, column=0)
        ### ================================================= gen_all_letters=================
        btn_doc = Button(pdfReportFrame, text='All Letters DOCX', font=('arial', 10, 'bold'),
                        bd=5, padx=0, pady=0, bg=btn_bg_color, fg=btn_font_color, height=1, width=18,
                        command=self.gen_all_letters)
        btn_doc.grid(row=0, column=1)
		
        btn_plots_all = Button(pdfReportFrame, text='Plots PDF all', font=('arial', 10, 'bold'),
                        bd=5, padx=0, pady=0, bg=btn_bg_color, fg=btn_font_color, height=1, width=18,
                        command=self.letter_plots_all_1)             #lambda: [f() for f in [self.letter_plots_all_1, self.letter_plots_all_2, self.letter_plots_all_3]])
        btn_plots_all.grid(row=0, column=2)

        btn_pdf_reports = Button(pdfReportFrame, text='PDF Reports', font=('arial', 10, 'bold'),
                        bd=5, padx=0, pady=0, bg=btn_bg_color, fg=btn_font_color, height=1, width=18,
                        command=self.letter_bh_jh_dv_plots)      #lambda: [f() for f in [self.letter_bh_jh_dv_plots, self.letter_wb_gr_si_reg_plots, self.ir_plots, self.summary_pages]])                         # self.pdf_reports
        btn_pdf_reports.grid(row=0, column=3)

        btn_home = Button(self, text="Back to Home",
                          command=lambda: controller.show_frame(StartPage))
        btn_home.pack(side=TOP)


    def OnDoubleClick(self, event):
        item = self.tree.selection()[0]
        c = self.tree.item(item, "text")
        col_labels=["SEM","SCADA","Err"]
        row_labels=["MU"]

        if c[-7:] == "(other)":
            sem_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][c[:-8]]
            scada_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][c[:-8]]
            err = self.controller.frames[StartPage].df_res_far["Error in %"][c[:-8]]
            table_vals=[[sem_mu, scada_mu, err]]
            fig, ax = plt.subplots()
            lines = []
            lns = []

            lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c[:-8]]), 'r', label='SEM', linewidth=1)
            line1 = lns1[0]
            lns.append(lns1)
            lines.append(line1)
            lns2 = ax.plot(self.controller.frames[StartPage].dff_scada_far_end[c[:-8]].index, abs(self.controller.frames[StartPage].dff_scada_far_end[c[:-8]]), 'b', label='SCADA', linewidth=1)
            line2 = lns2[0]
            lns.append(lns2)
            lines.append(line2)
            ax2 = ax.twinx()
            ax2.set_ylabel('Error in %', color='r')
            ax2.tick_params(axis='y', labelcolor='r')
            ax2.set_ylim(0,150)
            lns3 = ax2.plot(abs(self.controller.frames[StartPage].dff_sem_scada_far[c[:-8]]), alpha=0.8, color='green', label='SCADA ERROR', linewidth=1)
            line3 = lns3[0]
            lns.append(lns3)
            lines.append(line3)

            the_table = plt.table(cellText=table_vals,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.78,-0.285,0.24,0.13])
            the_table.auto_set_font_size(False)
            the_table.set_fontsize = 16

            ax.set_title(c)
            ax.set_ylabel('Flow (in MW)')
            ax.set_xlabel('Timestamp')
            plt.gcf().autofmt_xdate()
            lns = lns[0] + lns[1] + lns[2]
            labs = [l.get_label() for l in lns]
            leg = ax.legend(lns, labs, ncol=len(lines), loc='upper center', bbox_to_anchor=(0.5, -0.18), fancybox=True,
                            shadow=True)
            leg.get_frame().set_alpha(0.4)
            ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
            ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
            ax.minorticks_on()
            date_form = DateFormatter("%d %b %H:%M")
            ax.xaxis.set_major_formatter(date_form)
            plt.interactive(True)
            plt.tight_layout()

            lined = dict()
            for legline, origline in zip(leg.get_lines(), lines):
                legline.set_picker(5)  # 5 pts tolerance
                lined[legline] = origline

            def onpick(event):
                # on the pick event, find the orig line corresponding to the
                # legend proxy line, and toggle the visibility
                legline = event.artist
                origline = lined[legline]
                vis = not origline.get_visible()
                origline.set_visible(vis)
                # Change the alpha on the line in the legend so we can see what lines have been toggled
                if vis:
                    legline.set_alpha(1.0)
                else:
                    legline.set_alpha(0.2)
                fig.canvas.draw()

            fig.canvas.mpl_connect('pick_event', onpick)
            cursor = Cursor(ax, useblit=True, color='red', linewidth=1, horizOn=False, vertOn=True)
            plt.rcParams['axes.xmargin'] = 0
            plt.rcParams['axes.ymargin'] = 0
            plt.show(block=False)

        else:
            sem_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][c]
            scada_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][c]
            err = self.controller.frames[StartPage].df_res_to["Error in %"][c]
            table_vals=[[sem_mu, scada_mu, err]]
            fig, ax = plt.subplots()
            lines = []
            lns = []

            lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'r', label='SEM', linewidth=1)
            line1 = lns1[0]
            lines.append(line1)
            lns.append(lns1)
            lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
            line2 = lns2[0]
            lines.append(line2)
            lns.append(lns2)
            ax2 = ax.twinx()
            ax2.set_ylabel('Error in %', color='r')
            ax2.tick_params(axis='y', labelcolor='r')
            ax2.set_ylim(0,150)
            lns3 = ax2.plot(abs(self.controller.frames[StartPage].dff_sem_scada_to[c]), color='green', alpha=0.8, label='SCADA ERROR',linewidth=1)
            line3 = lns3[0]
            lines.append(line3)
            lns.append(lns3)

            the_table = plt.table(cellText=table_vals,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.78,-0.285,0.24,0.13])
            the_table.auto_set_font_size(False)
            the_table.set_fontsize = 16

            ax.set_title(c)
            ax.set_ylabel('Flow (in MW)')
            ax.set_xlabel('Timestamp')
            plt.gcf().autofmt_xdate()
            lns = lns[0] + lns[1] + lns[2]
            labs = [l.get_label() for l in lns]
            leg = ax.legend(lns, labs, ncol=len(lines), loc='upper center', bbox_to_anchor=(0.5, -0.18), fancybox=True,
                            shadow=True)
            leg.get_frame().set_alpha(0.4)
            ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
            ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
            ax.minorticks_on()
            date_form = DateFormatter("%d %b %H:%M")
            cursor = Cursor(ax, useblit=True, color='b', linewidth=2, horizOn=False, vertOn=True, alpha=0.5)
            ax.xaxis.set_major_formatter(date_form)
            plt.interactive(True)
            # plt.tight_layout()

            lined = dict()
            for legline, origline in zip(leg.get_lines(), lines):
                legline.set_picker(5)  # 5 pts tolerance
                lined[legline] = origline

            def onpick(event):
                # on the pick event, find the orig line corresponding to the
                # legend proxy line, and toggle the visibility
                legline = event.artist
                origline = lined[legline]
                vis = not origline.get_visible()
                origline.set_visible(vis)
                # Change the alpha on the line in the legend so we can see what lines have been toggled
                if vis:
                    legline.set_alpha(1.0)
                else:
                    legline.set_alpha(0.2)
                fig.canvas.draw()

            fig.canvas.mpl_connect('pick_event', onpick)
            #plt.text(1, 1, 'Error: {}'.format(err), fontsize = 15)
            plt.rcParams['axes.xmargin'] = 0
            plt.rcParams['axes.ymargin'] = 0
            plt.show(block=False)


    def callback(self, *args):
        c = self.variable.get()
        sem_mu_to = self.controller.frames[StartPage].df_res_to["SEM MU"][c]
        sem_mu_far = self.controller.frames[StartPage].df_res_far["SEM MU"][c]
        scada_mu_to = self.controller.frames[StartPage].df_res_to["SCADA MU"][c]
        scada_mu_far = self.controller.frames[StartPage].df_res_far["SCADA MU"][c]
        err_to = self.controller.frames[StartPage].df_res_to["Error in %"][c]
        err_far = self.controller.frames[StartPage].df_res_far["Error in %"][c]
        table_vals=[[sem_mu_to, scada_mu_to, err_to], [sem_mu_far, scada_mu_far, err_far]]
        col_labels=["SEM","SCADA","Err"]
        row_labels=["TO MU","FAR MU"]
        fig, ax = plt.subplots()
        lines = []

        lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'k', label='SEM TO END', linewidth=1)
        line1 = lns1[0]
        lines.append(line1)
        lns = lns1
        if ((c in self.controller.frames[StartPage].dff_sem_far_end.columns) and (abs(self.controller.frames[StartPage].dff_sem_far_end[c])).mean()>0):          # & (self.controller.frames[StartPage].dff_sem_far_end[c].isnull().all()==False):
            #print(self.controller.frames[StartPage].dff_sem_far_end[c].isnull().all())
            lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c]), 'y', label='SEM FAR END', linewidth=1)
            line2 = lns2[0]
            lines.append(line2)
            lns += lns2
        if c in self.controller.frames[StartPage].dff_scada_to_end.columns:
            lns3 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA TO END', linewidth=1)
            line3 = lns3[0]
            lines.append(line3)
            lns += lns3
        if ((c in self.controller.frames[StartPage].dff_scada_far_end.columns) and (abs(self.controller.frames[StartPage].dff_scada_far_end[c])).mean()>0):     # & (self.controller.frames[StartPage].dff_scada_far_end[c].isnull().all()==False ):
            lns4 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c]), 'g', label='SCADA FAR END',
                           linewidth=1)
            line4 = lns4[0]
            lines.append(line4)
            lns += lns4

        ax2 = ax.twinx()
        ax2.set_ylabel('Error in %', color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        ax2.set_ylim(0,100)
        if c in self.controller.frames[StartPage].dff_sem_scada_to.columns:
            lns5 = ax2.fill(abs(self.controller.frames[StartPage].dff_sem_scada_to[c]), color='red', alpha=0.2, label='SCADA TO END ERROR',
                            linewidth=1)
            line5 = lns5[0]
            lines.append(line5)
            lns += lns5
        if ((c in self.controller.frames[StartPage].dff_sem_scada_far.columns) and (abs(self.controller.frames[StartPage].dff_sem_far_end[c])).mean()>0):     # & (self.controller.frames[StartPage].dff_scada_far_end[c].isnull().all()==False):
            lns6 = ax2.plot(abs(self.controller.frames[StartPage].dff_sem_scada_far[c]), 'm', label='SCADA FAR END ERROR',
                            linewidth=1)
            
            line6 = lns6[0]
            lines.append(line6)
            lns += lns6

        the_table = plt.table(cellText=table_vals,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.78,-0.285,0.24,0.13])
        the_table.auto_set_font_size(False)
        the_table.set_fontsize = 16
        ax.set_title(c)
        ax.set_ylabel('Flow (in MW)')
        ax.set_xlabel('Timestamp')
        plt.gcf().autofmt_xdate()
        labs = [l.get_label() for l in lns]
        leg = ax.legend(lns, labs, ncol=3, loc='upper center', bbox_to_anchor=(0.5, -0.18), fancybox=True, shadow=True)
        leg.get_frame().set_alpha(0.4)
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
        ax.minorticks_on()
        date_form = DateFormatter("%d %b %H:%M")
        ax.xaxis.set_major_formatter(date_form)

        cursor = Cursor(ax, useblit=True, color='b', linewidth=2, horizOn=False, vertOn=True, alpha=0.5)

        lined = dict()
        for legline, origline in zip(leg.get_lines(), lines):
            legline.set_picker(5)  # 5 pts tolerance
            lined[legline] = origline

        def onpick(event):
            # on the pick event, find the orig line corresponding to the
            # legend proxy line, and toggle the visibility
            legline = event.artist
            origline = lined[legline]
            vis = not origline.get_visible()
            origline.set_visible(vis)
            # Change the alpha on the line in the legend so we can see what lines have been toggled
            if vis:
                legline.set_alpha(1.0)
            else:
                legline.set_alpha(0.2)
            fig.canvas.draw()

        fig.canvas.mpl_connect('pick_event', onpick)
        #plt.text(1, 1, err_str, fontsize = 15)
        plt.rcParams['axes.xmargin'] = 0
        plt.rcParams['axes.ymargin'] = 0
        plt.show(block=False)

#=================================================== Constituents letter generation in pdf part ============================================

    def letter_jharkhand(self):
        jh_list = self.controller.frames[StartPage].states["JH"]
        jh_list_1 = []
        for c in jh_list:
            if c[-7:] == "(other)":
                jh_list_1.append(rev_line_name(c[:-8]))
            else:
                jh_list_1.append(c)
        jh_list_1.sort(reverse=True)
        jh_list.sort(reverse=True)
        res_list = MyDialog(self, jh_list).getItemList()
        res_list_1 = MyDialog(self, jh_list_1).getItemList()
        day = date.today()
        today = day.strftime("%d-%m-%Y")
        File_object = open('''inputs/letter text files/jharkhand.txt''', "r")

        message = File_object.readlines()
        File_object.close()

        from itertools import groupby, zip_longest
        i = (list(g) for _, g in groupby(message, key='\n'.__ne__))
        file = ([a + b for a, b in zip_longest(i, i, fillvalue=[])])

        doc = SimpleDocTemplate("output/letters/Jharkhand_letter ({} to {}).pdf".format(
            self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')),
                                pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=108, bottomMargin=18)
        Story = []

        ref = file[0][0]
        address_parts = file[1]
        sub = file[2][0]
        dear = file[3][0]
        upper_body = file[4][0]
        lower_body = file[5][0]
        regard = file[6][0]
        faithful = file[7][0]
        authority = file[8][0]
        designation = file[9][0]
        copy = file[10][0]

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

        tbl_data = [
            [Paragraph("<font size=12>{}</font>".format(ref), styles["Normal"]),
             Paragraph("Date: {}".format(today), styles["Right"])]
        ]
        tbl = Table(tbl_data)
        Story.append(tbl)
        Story.append(Spacer(1, 12))

        # Create return address
        for part in address_parts:
            ptext = '<font size=12>{}</font>'.format(part.strip())
            Story.append(Paragraph(ptext, styles["Normal"]))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(sub)
        Story.append(Paragraph(ptext, styles["Center"]))
        Story.append(Spacer(1, 12))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(dear)
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>%s</font>' % (upper_body).format(
            start_date=self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            end_date=self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y'))
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        for part in res_list_1:
            tbl_data = [
                [Paragraph("", styles["Normal"]),
                 Paragraph("<font size=12><bullet>&bull;</bullet>{}</font>".format(part.strip()), styles["Normal"])]
            ]
            tbl = Table(tbl_data, colWidths=[0.3 * inch, 5 * inch])
            Story.append(tbl)
            Story.append(Spacer(1, 0))

        ptext = '<font size=12>{}</font>'.format(lower_body)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>{}</font>'.format(regard)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(faithful)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 24))
        ptext = '<font size=12><b>{}</b></font>'.format(authority)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 4))
        ptext = '<font size=12><b>{}</b></font>'.format(designation)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 64))

        ptext = '<font size=12>{}</font>'.format(copy)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        for c in res_list:
            if c[-7:] == "(other)":
                el = c[:-8]
            else:
                el = c
            sem_to_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][el]
            scada_to_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][el]
            err_to = self.controller.frames[StartPage].df_res_to["Error in %"][el]
            sem_far_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][el]
            scada_far_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][el]
            err_far = self.controller.frames[StartPage].df_res_far["Error in %"][el]
            col_labels=['SEM','SCADA','% Err']
            row_labels=['MU']
            table_vals_to = [[sem_to_mu, scada_to_mu, err_to]]
            table_vals_far = [[sem_far_mu, scada_far_mu, err_far]]
                
            if c[-7:] == "(other)":
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c[:-8]]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c[:-8]]), 'b', label='SCADA',
                               linewidth=1)
                lns.append(lns2)
                #===data table======
                the_table_far = plt.table(cellText=table_vals_far,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, fontsize=12, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_far.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].dff_sem_scada_far[c[:-8]]), 'r', label='ERROR', linewidth=1)
                #lns.append(lns3)

                ax.set_title(rev_line_name(c[:-8]))
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True, shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)
                # Story.append(Spacer(1, 24))

            else:
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
                lns.append(lns2)
                #===data table======
                the_table_to = plt.table(cellText=table_vals_to,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_to.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].dff_sem_scada_to[c]), 'r', label='SCADA ERROR', linewidth=1)
                #lns.append(lns3)

                ax.set_title(c)
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True,
                                shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)

        doc.build(Story)
        messagebox.showinfo('Letter generation', 'Jharkhand letter generated Successfully')

    def letter_PG_ER1(self):
        pg_er1_list = self.controller.frames[StartPage].states["PG_ER1"]
        pg_er1_list_1 = []
        for c in pg_er1_list:
            if c[-7:] == "(other)":
                pg_er1_list_1.append(rev_line_name(c[:-8]))
            else:
                pg_er1_list_1.append(c)
        pg_er1_list_1.sort(reverse=True)
        pg_er1_list.sort(reverse=True)
        res_list = MyDialog(self, pg_er1_list).getItemList()
        res_list_1 = MyDialog(self, pg_er1_list_1).getItemList()
        day = date.today()
        today = day.strftime("%d-%m-%Y")
        File_object = open('''inputs/letter text files/pg_er1.txt''', "r")

        message = File_object.readlines()
        File_object.close()

        from itertools import groupby, zip_longest
        i = (list(g) for _, g in groupby(message, key='\n'.__ne__))
        file = ([a + b for a, b in zip_longest(i, i, fillvalue=[])])

        doc = SimpleDocTemplate("output/letters/PG_ER1_letter ({} to {}).pdf".format(
            self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')),
                                pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=108, bottomMargin=18)
        Story = []

        ref = file[0][0]
        address_parts = file[1]
        sub = file[2][0]
        dear = file[3][0]
        upper_body = file[4][0]
        lower_body = file[5][0]
        regard = file[6][0]
        faithful = file[7][0]
        authority = file[8][0]
        designation = file[9][0]
        copy = file[10][0]

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

        tbl_data = [
            [Paragraph("<font size=12>{}</font>".format(ref), styles["Normal"]),
             Paragraph("Date: {}".format(today), styles["Right"])]
        ]
        tbl = Table(tbl_data)
        Story.append(tbl)
        Story.append(Spacer(1, 12))

        # Create return address
        for part in address_parts:
            ptext = '<font size=12>{}</font>'.format(part.strip())
            Story.append(Paragraph(ptext, styles["Normal"]))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(sub)
        Story.append(Paragraph(ptext, styles["Center"]))
        Story.append(Spacer(1, 12))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(dear)
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>%s</font>' % (upper_body).format(
            start_date=self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            end_date=self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y'))
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        for part in res_list_1:
            tbl_data = [
                [Paragraph("", styles["Normal"]),
                 Paragraph("<font size=12><bullet>&bull;</bullet>{}</font>".format(part.strip()), styles["Normal"])]
            ]
            tbl = Table(tbl_data, colWidths=[0.3 * inch, 5 * inch])
            Story.append(tbl)
            Story.append(Spacer(1, 0))

        ptext = '<font size=12>{}</font>'.format(lower_body)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>{}</font>'.format(regard)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(faithful)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 24))
        ptext = '<font size=12><b>{}</b></font>'.format(authority)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 4))
        ptext = '<font size=12><b>{}</b></font>'.format(designation)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 64))

        ptext = '<font size=12>{}</font>'.format(copy)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 24))

        for c in res_list:
            if c[-7:] == "(other)":
                el = c[:-8]
            else:
                el = c
            sem_to_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][el]
            scada_to_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][el]
            err_to = self.controller.frames[StartPage].df_res_to["Error in %"][el]
            sem_far_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][el]
            scada_far_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][el]
            err_far = self.controller.frames[StartPage].df_res_far["Error in %"][el]
            col_labels=['SEM','SCADA','% Err']
            row_labels=['MU']
            table_vals_to = [[sem_to_mu, scada_to_mu, err_to]]
            table_vals_far = [[sem_far_mu, scada_far_mu, err_far]]
            
            if c[-7:] == "(other)":
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c[:-8]]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c[:-8]]), 'b', label='SCADA',
                               linewidth=1)
                lns.append(lns2)
                #===data table ========
                the_table_far = plt.table(cellText=table_vals_far,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, fontsize=12, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_far.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].dff_sem_scada_far[c]), 'r', label='ERROR',linewidth=1)
                #lns.append(lns3)

                ax.set_title(rev_line_name(c[:-8]))
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True, shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)
                # Story.append(Spacer(1, 24))

            else:
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
                lns.append(lns2)
                #===data table======
                the_table_to = plt.table(cellText=table_vals_to,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_to.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].dff_sem_scada_to[c]), 'r', label='ERROR',linewidth=1)
                #lns.append(lns3)

                ax.set_title(c)
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True,
                                shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)

        doc.build(Story)
        messagebox.showinfo('Letter generation', 'PG-ER1 letter generated Successfully')

    def letter_PG_ER2(self):
        pg_er2_list = self.controller.frames[StartPage].states["PG_ER2"]
        pg_er2_list_1 = []
        for c in pg_er2_list:
            if c[-7:] == "(other)":
                pg_er2_list_1.append(rev_line_name(c[:-8]))
            else:
                pg_er2_list_1.append(c)
        pg_er2_list_1.sort(reverse=True)
        pg_er2_list.sort(reverse=True)
        res_list = MyDialog(self, pg_er2_list).getItemList()
        res_list_1 = MyDialog(self, pg_er2_list_1).getItemList()
        day = date.today()
        today = day.strftime("%d-%m-%Y")
        File_object = open('''inputs/letter text files/pg_er2.txt''', "r")

        message = File_object.readlines()
        File_object.close()

        from itertools import groupby, zip_longest
        i = (list(g) for _, g in groupby(message, key='\n'.__ne__))
        file = ([a + b for a, b in zip_longest(i, i, fillvalue=[])])

        doc = SimpleDocTemplate("output/letters/PG_ER2_letter ({} to {}).pdf".format(
            self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')),
                                pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=108, bottomMargin=18)
        Story = []

        ref = file[0][0]
        address_parts = file[1]
        sub = file[2][0]
        dear = file[3][0]
        upper_body = file[4][0]
        lower_body = file[5][0]
        regard = file[6][0]
        faithful = file[7][0]
        authority = file[8][0]
        designation = file[9][0]
        copy = file[10][0]

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

        tbl_data = [
            [Paragraph("<font size=12>{}</font>".format(ref), styles["Normal"]),
             Paragraph("Date: {}".format(today), styles["Right"])]
        ]
        tbl = Table(tbl_data)
        Story.append(tbl)
        Story.append(Spacer(1, 12))

        # Create return address
        for part in address_parts:
            ptext = '<font size=12>{}</font>'.format(part.strip())
            Story.append(Paragraph(ptext, styles["Normal"]))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(sub)
        Story.append(Paragraph(ptext, styles["Center"]))
        Story.append(Spacer(1, 12))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(dear)
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>%s</font>' % (upper_body).format(
            start_date=self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            end_date=self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y'))
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        for part in res_list_1:
            tbl_data = [
                [Paragraph("", styles["Normal"]),
                 Paragraph("<font size=12><bullet>&bull;</bullet>{}</font>".format(part.strip()), styles["Normal"])]
            ]
            tbl = Table(tbl_data, colWidths=[0.3 * inch, 5 * inch])
            Story.append(tbl)
            Story.append(Spacer(1, 0))

        ptext = '<font size=12>{}</font>'.format(lower_body)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>{}</font>'.format(regard)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(faithful)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 24))
        ptext = '<font size=12><b>{}</b></font>'.format(authority)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 4))
        ptext = '<font size=12><b>{}</b></font>'.format(designation)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 64))

        ptext = '<font size=12>{}</font>'.format(copy)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 24))

        for c in res_list:
            if c[-7:] == "(other)":
                el = c[:-8]
            else:
                el = c
            sem_to_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][el]
            scada_to_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][el]
            err_to = self.controller.frames[StartPage].df_res_to["Error in %"][el]
            sem_far_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][el]
            scada_far_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][el]
            err_far = self.controller.frames[StartPage].df_res_far["Error in %"][el]
            col_labels=['SEM','SCADA','% Err']
            row_labels=['MU']
            table_vals_to = [[sem_to_mu, scada_to_mu, err_to]]
            table_vals_far = [[sem_far_mu, scada_far_mu, err_far]]
            
            if c[-7:] == "(other)":
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c[:-8]]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c[:-8]]), 'b', label='SCADA',
                               linewidth=1)
                lns.append(lns2)
                #==== data table ========
                the_table_far = plt.table(cellText=table_vals_far,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, fontsize=12, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_far.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].dff_sem_scada_far[c]), 'r', label='ERROR',linewidth=1)
                #lns.append(lns3)

                ax.set_title(rev_line_name(c[:-8]))
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True, shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)
                # Story.append(Spacer(1, 24))

            else:
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
                lns.append(lns2)
                #==== data table ======
                the_table_to = plt.table(cellText=table_vals_to,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_to.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].dff_sem_scada_to[c]), 'r', label='ERROR', linewidth=1)
                #lns.append(lns3)

                ax.set_title(c)
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True,
                                shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)

        doc.build(Story)
        messagebox.showinfo('Letter generation', 'PG-ER2 letter generated Successfully')

    def letter_PG_ER3(self):
        pg_er3_list = self.controller.frames[StartPage].states["PG_odisha_project"]
        pg_er3_list_1 = []
        for c in pg_er3_list:
            if c[-7:] == "(other)":
                pg_er3_list_1.append(rev_line_name(c[:-8]))
            else:
                pg_er3_list_1.append(c)
        pg_er3_list_1.sort(reverse=True)
        pg_er3_list.sort(reverse=True)
        res_list = MyDialog(self, pg_er3_list).getItemList()
        res_list_1 = MyDialog(self, pg_er3_list_1).getItemList()
        day = date.today()
        today = day.strftime("%d-%m-%Y")
        File_object = open('''inputs/letter text files/pg_er1.txt''', "r")

        message = File_object.readlines()
        File_object.close()

        from itertools import groupby, zip_longest
        i = (list(g) for _, g in groupby(message, key='\n'.__ne__))
        file = ([a + b for a, b in zip_longest(i, i, fillvalue=[])])

        doc = SimpleDocTemplate("output/letters/PG_ER3_letter ({} to {}).pdf".format(
            self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')),
                                pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=108, bottomMargin=18)
        Story = []

        ref = file[0][0]
        address_parts = file[1]
        sub = file[2][0]
        dear = file[3][0]
        upper_body = file[4][0]
        lower_body = file[5][0]
        regard = file[6][0]
        faithful = file[7][0]
        authority = file[8][0]
        designation = file[9][0]
        copy = file[10][0]

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

        tbl_data = [
            [Paragraph("<font size=12>{}</font>".format(ref), styles["Normal"]),
             Paragraph("Date: {}".format(today), styles["Right"])]
        ]
        tbl = Table(tbl_data)
        Story.append(tbl)
        Story.append(Spacer(1, 12))

        # Create return address
        for part in address_parts:
            ptext = '<font size=12>{}</font>'.format(part.strip())
            Story.append(Paragraph(ptext, styles["Normal"]))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(sub)
        Story.append(Paragraph(ptext, styles["Center"]))
        Story.append(Spacer(1, 12))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(dear)
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>%s</font>' % (upper_body).format(
            start_date=self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            end_date=self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y'))
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        for part in res_list_1:
            tbl_data = [
                [Paragraph("", styles["Normal"]),
                 Paragraph("<font size=12><bullet>&bull;</bullet>{}</font>".format(part.strip()), styles["Normal"])]
            ]
            tbl = Table(tbl_data, colWidths=[0.3 * inch, 5 * inch])
            Story.append(tbl)
            Story.append(Spacer(1, 0))

        ptext = '<font size=12>{}</font>'.format(lower_body)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>{}</font>'.format(regard)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(faithful)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 24))
        ptext = '<font size=12><b>{}</b></font>'.format(authority)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 4))
        ptext = '<font size=12><b>{}</b></font>'.format(designation)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 64))

        ptext = '<font size=12>{}</font>'.format(copy)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 24))

        for c in res_list:
            if c[-7:] == "(other)":
                el = c[:-8]
            else:
                el = c
            sem_to_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][el]
            scada_to_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][el]
            err_to = self.controller.frames[StartPage].df_res_to["Error in %"][el]
            sem_far_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][el]
            scada_far_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][el]
            err_far = self.controller.frames[StartPage].df_res_far["Error in %"][el]
            col_labels=['SEM','SCADA','% Err']
            row_labels=['MU']
            table_vals_to = [[sem_to_mu, scada_to_mu, err_to]]
            table_vals_far = [[sem_far_mu, scada_far_mu, err_far]]
            
            if c[-7:] == "(other)":
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c[:-8]]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c[:-8]]), 'b', label='SCADA',
                               linewidth=1)
                lns.append(lns2)
                #====data table=====
                the_table_far = plt.table(cellText=table_vals_far,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, fontsize=12, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_far.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].dff_sem_scada_far[c]), 'r', label='ERROR',linewidth=1)
                #lns.append(lns3)

                ax.set_title(rev_line_name(c[:-8]))
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True, shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)
                # Story.append(Spacer(1, 24))

            else:
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
                lns.append(lns2)
                #===data table======
                the_table_to = plt.table(cellText=table_vals_to,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_to.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].dff_sem_scada_to[c]), 'r', label='ERROR',linewidth=1)
                #lns.append(lns3)

                ax.set_title(c)
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True,
                                shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)

        doc.build(Story)
        messagebox.showinfo('Letter generation', 'PG-ER3 letter generated Successfully')

    def letter_westbengal(self):
        wb_list = self.controller.frames[StartPage].states["WB"]
        wb_list_1 = []
        for c in wb_list:
            if c[-7:] == "(other)":
                wb_list_1.append(rev_line_name(c[:-8]))
            else:
                wb_list_1.append(c)
        wb_list_1.sort(reverse=True)
        wb_list.sort(reverse=True)
        res_list = MyDialog(self, wb_list).getItemList()
        res_list_1 = MyDialog(self, wb_list_1).getItemList()
        day = date.today()
        today = day.strftime("%d-%m-%Y")
        File_object = open('''inputs/letter text files/westbengal.txt''', "r")

        message = File_object.readlines()
        File_object.close()

        from itertools import groupby, zip_longest
        i = (list(g) for _, g in groupby(message, key='\n'.__ne__))
        file = ([a + b for a, b in zip_longest(i, i, fillvalue=[])])

        doc = SimpleDocTemplate("output/letters/WestBengal_letter ({} to {}).pdf".format(
            self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')),
                                pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=108, bottomMargin=18)
        Story = []

        ref = file[0][0]
        address_parts = file[1]
        sub = file[2][0]
        dear = file[3][0]
        upper_body = file[4][0]
        lower_body = file[5][0]
        regard = file[6][0]
        faithful = file[7][0]
        authority = file[8][0]
        designation = file[9][0]
        copy = file[10][0]

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

        tbl_data = [
            [Paragraph("<font size=12>{}</font>".format(ref), styles["Normal"]),
             Paragraph("Date: {}".format(today), styles["Right"])]
        ]
        tbl = Table(tbl_data)
        Story.append(tbl)
        Story.append(Spacer(1, 12))

        # Create return address
        for part in address_parts:
            ptext = '<font size=12>{}</font>'.format(part.strip())
            Story.append(Paragraph(ptext, styles["Normal"]))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(sub)
        Story.append(Paragraph(ptext, styles["Center"]))
        Story.append(Spacer(1, 12))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(dear)
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>%s</font>' % (upper_body).format(
            start_date=self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            end_date=self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y'))
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        for part in res_list_1:
            tbl_data = [
                [Paragraph("", styles["Normal"]),
                 Paragraph("<font size=12><bullet>&bull;</bullet>{}</font>".format(part.strip()), styles["Normal"])]
            ]
            tbl = Table(tbl_data, colWidths=[0.3 * inch, 5 * inch])
            Story.append(tbl)
            Story.append(Spacer(1, 0))

        ptext = '<font size=12>{}</font>'.format(lower_body)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>{}</font>'.format(regard)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(faithful)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 24))
        ptext = '<font size=12><b>{}</b></font>'.format(authority)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 4))
        ptext = '<font size=12><b>{}</b></font>'.format(designation)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 64))

        ptext = '<font size=12>{}</font>'.format(copy)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 24))

        for c in res_list:
            if c[-7:] == "(other)":
                el = c[:-8]
            else:
                el = c
            sem_to_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][el]
            scada_to_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][el]
            err_to = self.controller.frames[StartPage].df_res_to["Error in %"][el]
            sem_far_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][el]
            scada_far_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][el]
            err_far = self.controller.frames[StartPage].df_res_far["Error in %"][el]
            col_labels=['SEM','SCADA','% Err']
            row_labels=['MU']
            table_vals_to = [[sem_to_mu, scada_to_mu, err_to]]
            table_vals_far = [[sem_far_mu, scada_far_mu, err_far]]
            
            if c[-7:] == "(other)":
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c[:-8]]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c[:-8]]), 'b', label='SCADA',
                               linewidth=1)
                lns.append(lns2)
                #===== data table==========
                the_table_far = plt.table(cellText=table_vals_far,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, fontsize=12, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_far.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].dff_sem_scada_far[c[:-8]]), 'r', label='ERROR',linewidth=1)
                #lns.append(lns3)

                ax.set_title(rev_line_name(c[:-8]))
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True, shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)
                # Story.append(Spacer(1, 24))

            else:
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
                lns.append(lns2)
                #===data table======
                the_table_to = plt.table(cellText=table_vals_to,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_to.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].dff_sem_scada_to[c]), 'r', label='ERROR',linewidth=1)
                #lns.append(lns3)

                ax.set_title(c)
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True,
                                shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)

        doc.build(Story)
        messagebox.showinfo('Letter generation', 'West Bengal letter generated Successfully')

    def letter_bihar(self):
        bh_list = self.controller.frames[StartPage].states["BH"]
        bh_list_1 = []
        for c in bh_list:
            if c[-7:] == "(other)":
                bh_list_1.append(rev_line_name(c[:-8]))
            else:
                bh_list_1.append(c)
        bh_list_1.sort(reverse=True)
        bh_list.sort(reverse=True)
        res_list = MyDialog(self, bh_list).getItemList()
        res_list_1 = MyDialog(self, bh_list_1).getItemList()
        day = date.today()
        today = day.strftime("%d-%m-%Y")
        File_object = open('''inputs/letter text files/bihar.txt''', "r")

        message = File_object.readlines()
        File_object.close()

        from itertools import groupby, zip_longest
        i = (list(g) for _, g in groupby(message, key='\n'.__ne__))
        file = ([a + b for a, b in zip_longest(i, i, fillvalue=[])])

        doc = SimpleDocTemplate("output/letters/Bihar_letter ({} to {}).pdf".format(
            self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')),
                                pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=108, bottomMargin=18)
        Story = []

        ref = file[0][0]
        address_parts = file[1]
        sub = file[2][0]
        dear = file[3][0]
        upper_body = file[4][0]
        lower_body = file[5][0]
        regard = file[6][0]
        faithful = file[7][0]
        authority = file[8][0]
        designation = file[9][0]
        copy = file[10][0]

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

        tbl_data = [
            [Paragraph("<font size=12>{}</font>".format(ref), styles["Normal"]),
             Paragraph("Date: {}".format(today), styles["Right"])]
        ]
        tbl = Table(tbl_data)
        Story.append(tbl)
        Story.append(Spacer(1, 12))

        # Create return address
        for part in address_parts:
            ptext = '<font size=12>{}</font>'.format(part.strip())
            Story.append(Paragraph(ptext, styles["Normal"]))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(sub)
        Story.append(Paragraph(ptext, styles["Center"]))
        Story.append(Spacer(1, 12))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(dear)
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>%s</font>' % (upper_body).format(
            start_date=self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            end_date=self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y'))
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        for part in res_list_1:
            tbl_data = [
                [Paragraph("", styles["Normal"]),
                 Paragraph("<font size=12><bullet>&bull;</bullet>{}</font>".format(part.strip()), styles["Normal"])]
            ]
            tbl = Table(tbl_data, colWidths=[0.3 * inch, 5 * inch])
            Story.append(tbl)
            Story.append(Spacer(1, 0))

        ptext = '<font size=12>{}</font>'.format(lower_body)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>{}</font>'.format(regard)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(faithful)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 24))
        ptext = '<font size=12><b>{}</b></font>'.format(authority)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 4))
        ptext = '<font size=12><b>{}</b></font>'.format(designation)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 64))

        ptext = '<font size=12>{}</font>'.format(copy)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 24))

        for c in res_list:
            if c[-7:] == "(other)":
                el = c[:-8]
            else:
                el = c
            sem_to_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][el]
            scada_to_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][el]
            err_to = self.controller.frames[StartPage].df_res_to["Error in %"][el]
            sem_far_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][el]
            scada_far_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][el]
            err_far = self.controller.frames[StartPage].df_res_far["Error in %"][el]
            col_labels=['SEM','SCADA','% Err']
            row_labels=['MU']
            table_vals_to = [[sem_to_mu, scada_to_mu, err_to]]
            table_vals_far = [[sem_far_mu, scada_far_mu, err_far]]
            
            if c[-7:] == "(other)":
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c[:-8]]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c[:-8]]), 'b', label='SCADA',
                               linewidth=1)
                lns.append(lns2)
                #======= data table ========
                the_table_far = plt.table(cellText=table_vals_far,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, fontsize=12, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_far.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].df_sem_scada2[c[:-8]]), 'r', label='SCADA ERROR',linewidth=1)
                #lns.append(lns3)

                ax.set_title(rev_line_name(c[:-8]))
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True, shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)
                # Story.append(Spacer(1, 24))

            else:
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
                lns.append(lns2)
                #===data table======
                the_table_to = plt.table(cellText=table_vals_to,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_to.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].df_sem_scada1[c]), 'r', label='SCADA ERROR',linewidth=1)
                #lns.append(lns3)

                ax.set_title(c)
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True,
                                shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)

        doc.build(Story)
        messagebox.showinfo('Letter generation', 'Bihar letter generated Successfully at Desktop/tlc_report')

    def letter_dvc(self):
        dvc_list = self.controller.frames[StartPage].states["DV"]
        dvc_list_1 = []
        for c in dvc_list:
            if c[-7:] == "(other)":
                dvc_list_1.append(rev_line_name(c[:-8]))
            else:
                dvc_list_1.append(c)
        dvc_list_1.sort(reverse=True)
        dvc_list.sort(reverse=True)
        res_list = MyDialog(self, dvc_list).getItemList()
        res_list_1 = MyDialog(self, dvc_list_1).getItemList()
        day = date.today()
        today = day.strftime("%d-%m-%Y")
        File_object = open('''inputs/letter text files/dvc.txt''', "r")

        message = File_object.readlines()
        File_object.close()

        from itertools import groupby, zip_longest
        i = (list(g) for _, g in groupby(message, key='\n'.__ne__))
        file = ([a + b for a, b in zip_longest(i, i, fillvalue=[])])

        doc = SimpleDocTemplate("output/letters/DVC_letter ({} to {}).pdf".format(
            self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')),
                                pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=108, bottomMargin=18)
        Story = []

        ref = file[0][0]
        address_parts = file[1]
        sub = file[2][0]
        dear = file[3][0]
        upper_body = file[4][0]
        lower_body = file[5][0]
        regard = file[6][0]
        faithful = file[7][0]
        authority = file[8][0]
        designation = file[9][0]
        copy = file[10][0]

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

        tbl_data = [
            [Paragraph("<font size=12>{}</font>".format(ref), styles["Normal"]),
             Paragraph("Date: {}".format(today), styles["Right"])]
        ]
        tbl = Table(tbl_data)
        Story.append(tbl)
        Story.append(Spacer(1, 12))

        # Create return address
        for part in address_parts:
            ptext = '<font size=12>{}</font>'.format(part.strip())
            Story.append(Paragraph(ptext, styles["Normal"]))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(sub)
        Story.append(Paragraph(ptext, styles["Center"]))
        Story.append(Spacer(1, 12))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(dear)
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>%s</font>' % (upper_body).format(
            start_date=self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            end_date=self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y'))
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        for part in res_list_1:
            tbl_data = [
                [Paragraph("", styles["Normal"]),
                 Paragraph("<font size=12><bullet>&bull;</bullet>{}</font>".format(part.strip()), styles["Normal"])]
            ]
            tbl = Table(tbl_data, colWidths=[0.3 * inch, 5 * inch])
            Story.append(tbl)
            Story.append(Spacer(1, 0))

        ptext = '<font size=12>{}</font>'.format(lower_body)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>{}</font>'.format(regard)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(faithful)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 24))
        ptext = '<font size=12><b>{}</b></font>'.format(authority)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 4))
        ptext = '<font size=12><b>{}</b></font>'.format(designation)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 64))

        ptext = '<font size=12>{}</font>'.format(copy)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 24))

        for c in res_list:
            if c[-7:] == "(other)":
                el = c[:-8]
            else:
                el = c
            sem_to_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][el]
            scada_to_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][el]
            err_to = self.controller.frames[StartPage].df_res_to["Error in %"][el]
            sem_far_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][el]
            scada_far_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][el]
            err_far = self.controller.frames[StartPage].df_res_far["Error in %"][el]
            col_labels=['SEM','SCADA','% Err']
            row_labels=['MU']
            table_vals_to = [[sem_to_mu, scada_to_mu, err_to]]
            table_vals_far = [[sem_far_mu, scada_far_mu, err_far]]
            
            if c[-7:] == "(other)":
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c[:-8]]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c[:-8]]), 'b', label='SCADA',
                               linewidth=1)
                lns.append(lns2)
                #===== data table=======
                the_table_far = plt.table(cellText=table_vals_far,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, fontsize=12, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_far.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].df_sem_scada2[c[:-8]]), 'r', label='SCADA ERROR',linewidth=1)
                #lns.append(lns3)

                ax.set_title(rev_line_name(c[:-8]))
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True, shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)
                # Story.append(Spacer(1, 24))

            else:
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
                lns.append(lns2)
                #===data table======
                the_table_to = plt.table(cellText=table_vals_to,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_to.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].df_sem_scada1[c]), 'r', label='SCADA ERROR',linewidth=1)
                #lns.append(lns3)

                ax.set_title(c)
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True,
                                shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)

        doc.build(Story)
        messagebox.showinfo('Letter generation', 'DVC letter generated Successfully at Desktop/tlc_report')

    def letter_odisha(self):
        gr_list = self.controller.frames[StartPage].states["GR"]
        gr_list_1 = []
        for c in gr_list:
            if c[-7:] == "(other)":
                gr_list_1.append(rev_line_name(c[:-8]))
            else:
                gr_list_1.append(c)
        gr_list_1.sort(reverse=True)
        gr_list.sort(reverse=True)
        res_list = MyDialog(self, gr_list).getItemList()
        res_list_1 = MyDialog(self, gr_list_1).getItemList()
        day = date.today()
        today = day.strftime("%d-%m-%Y")
        File_object = open('''inputs/letter text files/odisha.txt''', "r")

        message = File_object.readlines()
        File_object.close()

        from itertools import groupby, zip_longest
        i = (list(g) for _, g in groupby(message, key='\n'.__ne__))
        file = ([a + b for a, b in zip_longest(i, i, fillvalue=[])])

        doc = SimpleDocTemplate("output/letters/Odisha_letter ({} to {}).pdf".format(
            self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')),
                                pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=108, bottomMargin=18)
        Story = []

        ref = file[0][0]
        address_parts = file[1]
        sub = file[2][0]
        dear = file[3][0]
        upper_body = file[4][0]
        lower_body = file[5][0]
        regard = file[6][0]
        faithful = file[7][0]
        authority = file[8][0]
        designation = file[9][0]
        copy = file[10][0]

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

        tbl_data = [
            [Paragraph("<font size=12>{}</font>".format(ref), styles["Normal"]),
             Paragraph("Date: {}".format(today), styles["Right"])]
        ]
        tbl = Table(tbl_data)
        Story.append(tbl)
        Story.append(Spacer(1, 12))

        # Create return address
        for part in address_parts:
            ptext = '<font size=12>{}</font>'.format(part.strip())
            Story.append(Paragraph(ptext, styles["Normal"]))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(sub)
        Story.append(Paragraph(ptext, styles["Center"]))
        Story.append(Spacer(1, 12))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(dear)
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>%s</font>' % (upper_body).format(
            start_date=self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            end_date=self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y'))
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        for part in res_list_1:
            tbl_data = [
                [Paragraph("", styles["Normal"]),
                 Paragraph("<font size=12><bullet>&bull;</bullet>{}</font>".format(part.strip()), styles["Normal"])]
            ]
            tbl = Table(tbl_data, colWidths=[0.3 * inch, 5 * inch])
            Story.append(tbl)
            Story.append(Spacer(1, 0))

        ptext = '<font size=12>{}</font>'.format(lower_body)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>{}</font>'.format(regard)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(faithful)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 24))
        ptext = '<font size=12><b>{}</b></font>'.format(authority)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 4))
        ptext = '<font size=12><b>{}</b></font>'.format(designation)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 64))

        ptext = '<font size=12>{}</font>'.format(copy)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 24))

        for c in res_list:
            if c[-7:] == "(other)":
                el = c[:-8]
            else:
                el = c
            sem_to_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][el]
            scada_to_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][el]
            err_to = self.controller.frames[StartPage].df_res_to["Error in %"][el]
            sem_far_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][el]
            scada_far_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][el]
            err_far = self.controller.frames[StartPage].df_res_far["Error in %"][el]
            col_labels=['SEM','SCADA','% Err']
            row_labels=['MU']
            table_vals_to = [[sem_to_mu, scada_to_mu, err_to]]
            table_vals_far = [[sem_far_mu, scada_far_mu, err_far]]
            
            if c[-7:] == "(other)":
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c[:-8]]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c[:-8]]), 'b', label='SCADA',
                               linewidth=1)
                lns.append(lns2)
                #===== data table ========================
                the_table_far = plt.table(cellText=table_vals_far,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, fontsize=12, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_far.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].df_sem_scada2[c[:-8]]), 'r', label='SCADA ERROR',linewidth=1)
                #lns.append(lns3)

                ax.set_title(rev_line_name(c[:-8]))
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True, shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)
                # Story.append(Spacer(1, 24))

            else:
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
                lns.append(lns2)
                #===data table======
                the_table_to = plt.table(cellText=table_vals_to,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_to.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].df_sem_scada1[c]), 'r', label='SCADA ERROR',linewidth=1)
                #lns.append(lns3)

                ax.set_title(c)
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True,
                                shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)

        doc.build(Story)
        messagebox.showinfo('Letter generation', 'Odisha letter generated Successfully at Desktop/tlc_report')

    def letter_sikkim(self):
        si_list = self.controller.frames[StartPage].states["SI"]
        si_list_1 = []
        for c in si_list:
            if c[-7:] == "(other)":
                si_list_1.append(rev_line_name(c[:-8]))
            else:
                si_list_1.append(c)
        si_list_1.sort(reverse=True)
        si_list.sort(reverse=True)
        res_list = MyDialog(self, si_list).getItemList()
        res_list_1 = MyDialog(self, si_list_1).getItemList()
        day = date.today()
        today = day.strftime("%d-%m-%Y")
        File_object = open('''inputs/letter text files/sikkim.txt''', "r")

        message = File_object.readlines()
        File_object.close()

        from itertools import groupby, zip_longest
        i = (list(g) for _, g in groupby(message, key='\n'.__ne__))
        file = ([a + b for a, b in zip_longest(i, i, fillvalue=[])])

        doc = SimpleDocTemplate("output/letters/Sikkim_letter ({} to {}).pdf".format(
            self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')),
                                pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=108, bottomMargin=18)
        Story = []

        ref = file[0][0]
        address_parts = file[1]
        sub = file[2][0]
        dear = file[3][0]
        upper_body = file[4][0]
        lower_body = file[5][0]
        regard = file[6][0]
        faithful = file[7][0]
        authority = file[8][0]
        designation = file[9][0]
        copy = file[10][0]

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

        tbl_data = [
            [Paragraph("<font size=12>{}</font>".format(ref), styles["Normal"]),
             Paragraph("Date: {}".format(today), styles["Right"])]
        ]
        tbl = Table(tbl_data)
        Story.append(tbl)
        Story.append(Spacer(1, 12))

        # Create return address
        for part in address_parts:
            ptext = '<font size=12>{}</font>'.format(part.strip())
            Story.append(Paragraph(ptext, styles["Normal"]))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(sub)
        Story.append(Paragraph(ptext, styles["Center"]))
        Story.append(Spacer(1, 12))

        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(dear)
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>%s</font>' % (upper_body).format(
            start_date=self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            end_date=self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y'))
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        for part in res_list_1:
            tbl_data = [
                [Paragraph("", styles["Normal"]),
                 Paragraph("<font size=12><bullet>&bull;</bullet>{}</font>".format(part.strip()), styles["Normal"])]
            ]
            tbl = Table(tbl_data, colWidths=[0.3 * inch, 5 * inch])
            Story.append(tbl)
            Story.append(Spacer(1, 0))

        ptext = '<font size=12>{}</font>'.format(lower_body)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))

        ptext = '<font size=12>{}</font>'.format(regard)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 12))
        ptext = '<font size=12>{}</font>'.format(faithful)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 24))
        ptext = '<font size=12><b>{}</b></font>'.format(authority)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 4))
        ptext = '<font size=12><b>{}</b></font>'.format(designation)
        Story.append(Paragraph(ptext, styles["Right"]))
        Story.append(Spacer(1, 64))

        ptext = '<font size=12>{}</font>'.format(copy)
        Story.append(Paragraph(ptext, styles["Justify"]))
        Story.append(Spacer(1, 24))

        for c in res_list:
            if c[-7:] == "(other)":
                el = c[:-8]
            else:
                el = c
            sem_to_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][el]
            scada_to_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][el]
            err_to = self.controller.frames[StartPage].df_res_to["Error in %"][el]
            sem_far_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][el]
            scada_far_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][el]
            err_far = self.controller.frames[StartPage].df_res_far["Error in %"][el]
            col_labels=['SEM','SCADA','% Err']
            row_labels=['MU']
            table_vals_to = [[sem_to_mu, scada_to_mu, err_to]]
            table_vals_far = [[sem_far_mu, scada_far_mu, err_far]]
            
            if c[-7:] == "(other)":
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c[:-8]]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c[:-8]]), 'b', label='SCADA',
                               linewidth=1)
                lns.append(lns2)
                #==== data table ======
                the_table_far = plt.table(cellText=table_vals_far,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, fontsize=12, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_far.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].df_sem_scada2[c[:-8]]), 'r', label='SCADA ERROR',linewidth=1)
                #lns.append(lns3)

                ax.set_title(rev_line_name(c[:-8]))
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True, shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)
                # Story.append(Spacer(1, 24))

            else:
                fig, ax = plt.subplots()
                lns = []

                lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'r', label='SEM', linewidth=1)
                lns.append(lns1)
                lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
                lns.append(lns2)
                #===data table======
                the_table_to = plt.table(cellText=table_vals_to,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                the_table_to.set_fontsize = 12
                #ax2 = ax.twinx()
                #ax2.set_ylabel('Error in %', color='r')
                #ax2.tick_params(axis='y', labelcolor='r')
                #lns3 = ax2.plot(abs(self.controller.frames[StartPage].df_sem_scada1[c]), 'r', label='SCADA ERROR',linewidth=1)
                #lns.append(lns3)

                ax.set_title(c)
                ax.set_ylabel('Flow (in MW)')
                ax.set_xlabel('Timestamp')
                plt.gcf().autofmt_xdate()
                lns = lns[0] + lns[1]# + lns[2]
                labs = [l.get_label() for l in lns]
                leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                                fancybox=True,
                                shadow=True)
                leg.get_frame().set_alpha(0.4)
                ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                ax.minorticks_on()
                date_form = DateFormatter("%d %b %H:%M")
                ax.xaxis.set_major_formatter(date_form)
                plt.margins(0, 0)

                img = PdfImage(fig, width=500, height=300)
                plt.close(fig='all')
                Story.append(img)

        doc.build(Story)
        messagebox.showinfo('Letter generation', 'Sikkim letter generated Successfully at Desktop/tlc_report')


    def wb_calc(self):
        dt1 = self.controller.frames[StartPage].cal_start.get_date()
        dt2 = self.controller.frames[StartPage].cal_end.get_date()

        try:
            start_dt = self.controller.frames[StartPage].cal_start.get_date().strftime("%d%m%Y")
            end_dt = (self.controller.frames[StartPage].cal_start.get_date() + timedelta(days=6)).strftime("%d%m%Y")
            month_folder = self.controller.frames[StartPage].cal_start.get_date().strftime("%b %y")
            year_folder = self.controller.frames[StartPage].cal_start.get_date().strftime("%Y")
            try:
                os.makedirs('output/reports/{}'.format(year_folder))
            except FileExistsError:
                pass
            try:
                os.makedirs('output/reports/{}/{}'.format(year_folder, month_folder))
            except FileExistsError:
                pass
        except:
            pass
        engine = sqlalchemy.create_engine('mysql+pymysql://sunil:ERLDC$cada123@10.3.101.90:3306/amr_data')
        self.dff_sem_to_end = pd.read_sql_query("SELECT * FROM sem_to_end_{} WHERE Date BETWEEN '{}' AND '{}'".format(dt1.strftime("%Y"),dt1.strftime("%Y-%m-%d") + ' 00:00',dt2.strftime("%Y-%m-%d") + ' 23:45'),engine, index_col='Date')
        self.dff_sem_far_end = pd.read_sql_query("SELECT * FROM sem_far_end_{} WHERE Date BETWEEN '{}' AND '{}'".format(dt1.strftime("%Y"),dt1.strftime("%Y-%m-%d") + ' 00:00',dt2.strftime("%Y-%m-%d") + ' 23:45'),engine, index_col='Date')
        self.dff_scada_to_end = pd.read_sql_query("SELECT * FROM scada_to_end_{} WHERE Date BETWEEN '{}' AND '{}'".format(dt1.strftime("%Y"),dt1.strftime("%Y-%m-%d") + ' 00:00',dt2.strftime("%Y-%m-%d") + ' 23:45'),engine, index_col='Date')
        self.dff_scada_far_end = pd.read_sql_query("SELECT * FROM scada_far_end_{} WHERE Date BETWEEN '{}' AND '{}'".format(dt1.strftime("%Y"),dt1.strftime("%Y-%m-%d") + ' 00:00',dt2.strftime("%Y-%m-%d") + ' 23:45'),engine, index_col='Date')
            
        conn = pymysql.connect(host='10.3.101.90', port=3306, user='sunil', passwd='ERLDC$cada123', db='amr_data')
        cur = conn.cursor()
        cur.execute("select feeder_name from master_mapping WHERE (feeder_from='WB' OR to_feeder='WB') AND Calc='To'")
        cols_to_list = []
        cols_far_list = []
        err = {}
        for row in cur:
            cols_to_list.append(row[0])
        cur.close()

        cur = conn.cursor()
        cur.execute("select feeder_name from master_mapping WHERE (feeder_from='WB' OR to_feeder='WB') AND Calc='Far'")
        for row in cur:
            cols_far_list.append(row[0])
        cur.close()
        conn.close()

        cols_to_list.append("WB_DRAWAL")
            
        self.df_sem_to_end_wb = self.dff_sem_to_end[cols_to_list]
        self.df_sem_far_end_wb = self.dff_sem_far_end[cols_far_list]
        self.df_scada_to_end_wb = self.dff_scada_to_end[cols_to_list]
        self.df_scada_far_end_wb = self.dff_scada_far_end[cols_far_list]

        self.df_sem_wb = self.df_sem_to_end_wb.merge(self.df_sem_far_end_wb, left_index=True, right_index=True)
        self.df_scada_wb = self.df_scada_to_end_wb.merge(self.df_scada_far_end_wb, left_index=True, right_index=True)
        self.sem_scada_wb = self.df_sem_wb - self.df_scada_wb

        wb_dfs = {"WB_SEM":self.df_sem_wb, "WB_SCADA":self.df_scada_wb, "WB_SEM_SCADA":self.sem_scada_wb}

        writer = pd.ExcelWriter('output/reports/{}/{}/{}_to_{}_TLC_WB.xlsx'.format(year_folder, month_folder, start_dt, end_dt),engine='openpyxl')
        #writer.book = book
        for sheet_name in wb_dfs.keys():
            wb_dfs[sheet_name].to_excel(writer, sheet_name=sheet_name)
            
        #writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        writer.save()
        messagebox.showinfo('Report generation', 'Report generated successfully')
        
        #self.dff_sem_to_end.fillna(0, inplace=True)
        #self.dff_sem_far_end.fillna(0, inplace=True)
        #self.dff_scada_to_end.fillna(0, inplace=True)
        #self.dff_scada_far_end.fillna(0, inplace=True)
		    
        #df_sem_to = self.dff_sem_to_end.copy()
        #df_sem_far = self.dff_sem_far_end.copy()
        #df_scada_to = self.dff_scada_to_end.copy()
        #df_scada_far = self.dff_scada_far_end.copy()
            
        #df_sem_to.fillna(0, inplace=True)
        #df_sem_far.fillna(0, inplace=True)
        #df_scada_to.fillna(0, inplace=True)
        #df_scada_far.fillna(0, inplace=True)


    def wb_constituent(self):
        dt1 = self.controller.frames[StartPage].cal_start.get_date()
        dt2 = self.controller.frames[StartPage].cal_end.get_date()

        try:
            start_dt = self.controller.frames[StartPage].cal_start.get_date().strftime("%d%m%Y")
            end_dt = (self.controller.frames[StartPage].cal_start.get_date() + timedelta(days=6)).strftime("%d%m%Y")
            month_folder = self.controller.frames[StartPage].cal_start.get_date().strftime("%b %y")
            year_folder = self.controller.frames[StartPage].cal_start.get_date().strftime("%Y")
            try:
                os.makedirs('output/reports/{}'.format(year_folder))
            except FileExistsError:
                pass
            try:
                os.makedirs('output/reports/{}/{}'.format(year_folder, month_folder))
            except FileExistsError:
                pass
        except:
            pass
        engine = sqlalchemy.create_engine('mysql+pymysql://sunil:ERLDC$cada123@10.3.101.90:3306/amr_data')
        self.dff_sem_to_end = pd.read_sql_query("SELECT * FROM sem_to_end_{} WHERE Date BETWEEN '{}' AND '{}'".format(dt1.strftime("%Y"),dt1.strftime("%Y-%m-%d") + ' 00:00',dt2.strftime("%Y-%m-%d") + ' 23:45'),engine, index_col='Date')
        self.dff_sem_far_end = pd.read_sql_query("SELECT * FROM sem_far_end_{} WHERE Date BETWEEN '{}' AND '{}'".format(dt1.strftime("%Y"),dt1.strftime("%Y-%m-%d") + ' 00:00',dt2.strftime("%Y-%m-%d") + ' 23:45'),engine, index_col='Date')
        self.dff_scada_to_end = pd.read_sql_query("SELECT * FROM scada_to_end_{} WHERE Date BETWEEN '{}' AND '{}'".format(dt1.strftime("%Y"),dt1.strftime("%Y-%m-%d") + ' 00:00',dt2.strftime("%Y-%m-%d") + ' 23:45'),engine, index_col='Date')
        self.dff_scada_far_end = pd.read_sql_query("SELECT * FROM scada_far_end_{} WHERE Date BETWEEN '{}' AND '{}'".format(dt1.strftime("%Y"),dt1.strftime("%Y-%m-%d") + ' 00:00',dt2.strftime("%Y-%m-%d") + ' 23:45'),engine, index_col='Date')

        ################################## WB DATA ########################################################################################################    
        conn = pymysql.connect(host='10.3.101.90', port=3306, user='sunil', passwd='ERLDC$cada123', db='amr_data')
        cur = conn.cursor()
        cur.execute("select feeder_name from master_mapping WHERE feeder_from='WB'")
        cols_to_list_wb = []
        cols_far_list_wb = []
        err = {}
        for row in cur:
            cols_to_list_wb.append(row[0])
        cur.close()

        cur = conn.cursor()
        cur.execute("select feeder_name from master_mapping WHERE to_feeder='WB'")
        for row in cur:
            cols_far_list_wb.append(row[0])
        cur.close()
        conn.close()

        cols_to_list_wb.append("WB_DRAWAL")
            
        self.df_sem_to_end_wb = self.dff_sem_to_end[cols_to_list_wb]
        self.df_sem_far_end_wb = self.dff_sem_far_end[cols_far_list_wb]
        self.df_scada_to_end_wb = self.dff_scada_to_end[cols_to_list_wb]
        self.df_scada_far_end_wb = self.dff_scada_far_end[cols_far_list_wb]

        self.df_sem_wb = self.df_sem_to_end_wb.merge(self.df_sem_far_end_wb, left_index=True, right_index=True)
        self.df_scada_wb = self.df_scada_to_end_wb.merge(self.df_scada_far_end_wb, left_index=True, right_index=True)
        self.sem_scada_wb = self.df_sem_wb - self.df_scada_wb

        wb_dfs = {"WB_SEM":self.df_sem_wb, "WB_SCADA":self.df_scada_wb, "WB_SEM_SCADA":self.sem_scada_wb}

        writer = pd.ExcelWriter('output/reports/{}/{}/{}_to_{}_TLC_WB_const.xlsx'.format(year_folder, month_folder, start_dt, end_dt),engine='openpyxl')
        #writer.book = book
        for sheet_name in wb_dfs.keys():
            wb_dfs[sheet_name].to_excel(writer, sheet_name=sheet_name)
            
        #writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        writer.save()
        messagebox.showinfo('Report generation', 'WB Report generated successfully')

        ################################## BH DATA ########################################################################################################    
        conn = pymysql.connect(host='10.3.101.90', port=3306, user='sunil', passwd='ERLDC$cada123', db='amr_data')
        cur = conn.cursor()
        cur.execute("select feeder_name from master_mapping WHERE feeder_from='BH'")
        cols_to_list_bh = []
        cols_far_list_bh = []
        err = {}
        for row in cur:
            cols_to_list_bh.append(row[0])
        cur.close()

        cur = conn.cursor()
        cur.execute("select feeder_name from master_mapping WHERE to_feeder='BH'")
        for row in cur:
            cols_far_list_bh.append(row[0])
        cur.close()
        conn.close()

        cols_to_list_bh.append("BH_DRAWAL")
            
        self.df_sem_to_end_bh = self.dff_sem_to_end[cols_to_list_bh]
        self.df_sem_far_end_bh = self.dff_sem_far_end[cols_far_list_bh]
        self.df_scada_to_end_bh = self.dff_scada_to_end[cols_to_list_bh]
        self.df_scada_far_end_bh = self.dff_scada_far_end[cols_far_list_bh]

        self.df_sem_bh = self.df_sem_to_end_bh.merge(self.df_sem_far_end_bh, left_index=True, right_index=True)
        self.df_scada_bh = self.df_scada_to_end_bh.merge(self.df_scada_far_end_bh, left_index=True, right_index=True)
        self.sem_scada_bh = self.df_sem_bh - self.df_scada_bh

        bh_dfs = {"BH_SEM":self.df_sem_bh, "BH_SCADA":self.df_scada_bh, "BH_SEM_SCADA":self.sem_scada_bh}

        writer = pd.ExcelWriter('output/reports/{}/{}/{}_to_{}_TLC_BH_const.xlsx'.format(year_folder, month_folder, start_dt, end_dt),engine='openpyxl')
        #writer.book = book
        for sheet_name in bh_dfs.keys():
            bh_dfs[sheet_name].to_excel(writer, sheet_name=sheet_name)
            
        #writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        writer.save()
        messagebox.showinfo('Report generation', 'BH Report generated successfully')

        ################################## JH DATA ########################################################################################################    
        conn = pymysql.connect(host='10.3.101.90', port=3306, user='sunil', passwd='ERLDC$cada123', db='amr_data')
        cur = conn.cursor()
        cur.execute("select feeder_name from master_mapping WHERE feeder_from='JH'")
        cols_to_list_jh = []
        cols_far_list_jh = []
        err = {}
        for row in cur:
            cols_to_list_jh.append(row[0])
        cur.close()

        cur = conn.cursor()
        cur.execute("select feeder_name from master_mapping WHERE to_feeder='JH'")
        for row in cur:
            cols_far_list_jh.append(row[0])
        cur.close()
        conn.close()

        cols_to_list_jh.append("JH_DRAWAL")
            
        self.df_sem_to_end_jh = self.dff_sem_to_end[cols_to_list_jh]
        self.df_sem_far_end_jh = self.dff_sem_far_end[cols_far_list_jh]
        self.df_scada_to_end_jh = self.dff_scada_to_end[cols_to_list_jh]
        self.df_scada_far_end_jh = self.dff_scada_far_end[cols_far_list_jh]

        self.df_sem_jh = self.df_sem_to_end_jh.merge(self.df_sem_far_end_jh, left_index=True, right_index=True)
        self.df_scada_jh = self.df_scada_to_end_jh.merge(self.df_scada_far_end_jh, left_index=True, right_index=True)
        self.sem_scada_jh = self.df_sem_jh - self.df_scada_jh

        jh_dfs = {"JH_SEM":self.df_sem_jh, "JH_SCADA":self.df_scada_jh, "JH_SEM_SCADA":self.sem_scada_jh}

        writer = pd.ExcelWriter('output/reports/{}/{}/{}_to_{}_TLC_JH_const.xlsx'.format(year_folder, month_folder, start_dt, end_dt),engine='openpyxl')
        #writer.book = book
        for sheet_name in jh_dfs.keys():
            jh_dfs[sheet_name].to_excel(writer, sheet_name=sheet_name)
            
        #writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        writer.save()
        messagebox.showinfo('Report generation', 'JH Report generated successfully')

        ################################## DVC DATA ########################################################################################################    
        conn = pymysql.connect(host='10.3.101.90', port=3306, user='sunil', passwd='ERLDC$cada123', db='amr_data')
        cur = conn.cursor()
        cur.execute("select feeder_name from master_mapping WHERE feeder_from='DV'")
        cols_to_list_dv = []
        cols_far_list_dv = []
        err = {}
        for row in cur:
            cols_to_list_dv.append(row[0])
        cur.close()

        cur = conn.cursor()
        cur.execute("select feeder_name from master_mapping WHERE to_feeder='DV'")
        for row in cur:
            cols_far_list_dv.append(row[0])
        cur.close()
        conn.close()

        cols_to_list_dv.append("DV_DRAWAL")
            
        self.df_sem_to_end_dv = self.dff_sem_to_end[cols_to_list_dv]
        self.df_sem_far_end_dv = self.dff_sem_far_end[cols_far_list_dv]
        self.df_scada_to_end_dv = self.dff_scada_to_end[cols_to_list_dv]
        self.df_scada_far_end_dv = self.dff_scada_far_end[cols_far_list_dv]

        self.df_sem_dv = self.df_sem_to_end_dv.merge(self.df_sem_far_end_dv, left_index=True, right_index=True)
        self.df_scada_dv = self.df_scada_to_end_dv.merge(self.df_scada_far_end_dv, left_index=True, right_index=True)
        self.sem_scada_dv = self.df_sem_dv - self.df_scada_dv

        dv_dfs = {"DV_SEM":self.df_sem_dv, "DV_SCADA":self.df_scada_dv, "DV_SEM_SCADA":self.sem_scada_dv}

        writer = pd.ExcelWriter('output/reports/{}/{}/{}_to_{}_TLC_DV_const.xlsx'.format(year_folder, month_folder, start_dt, end_dt),engine='openpyxl')
        #writer.book = book
        for sheet_name in dv_dfs.keys():
            dv_dfs[sheet_name].to_excel(writer, sheet_name=sheet_name)
            
        #writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        writer.save()
        messagebox.showinfo('Report generation', 'DVC Report generated successfully')

        ################################## Odisha DATA ########################################################################################################    
        conn = pymysql.connect(host='10.3.101.90', port=3306, user='sunil', passwd='ERLDC$cada123', db='amr_data')
        cur = conn.cursor()
        cur.execute("select feeder_name from master_mapping WHERE feeder_from='GR'")
        cols_to_list_gr = []
        cols_far_list_gr = []
        err = {}
        for row in cur:
            cols_to_list_gr.append(row[0])
        cur.close()

        cur = conn.cursor()
        cur.execute("select feeder_name from master_mapping WHERE to_feeder='GR'")
        for row in cur:
            cols_far_list_gr.append(row[0])
        cur.close()
        conn.close()

        cols_to_list_gr.append("GR_DRAWAL")
            
        self.df_sem_to_end_gr = self.dff_sem_to_end[cols_to_list_gr]
        self.df_sem_far_end_gr = self.dff_sem_far_end[cols_far_list_gr]
        self.df_scada_to_end_gr = self.dff_scada_to_end[cols_to_list_gr]
        self.df_scada_far_end_gr = self.dff_scada_far_end[cols_far_list_gr]

        self.df_sem_gr = self.df_sem_to_end_gr.merge(self.df_sem_far_end_gr, left_index=True, right_index=True)
        self.df_scada_gr = self.df_scada_to_end_gr.merge(self.df_scada_far_end_gr, left_index=True, right_index=True)
        self.sem_scada_gr = self.df_sem_gr - self.df_scada_gr

        gr_dfs = {"GR_SEM":self.df_sem_gr, "GR_SCADA":self.df_scada_gr, "GR_SEM_SCADA":self.sem_scada_gr}

        writer = pd.ExcelWriter('output/reports/{}/{}/{}_to_{}_TLC_GR_const.xlsx'.format(year_folder, month_folder, start_dt, end_dt),engine='openpyxl')
        #writer.book = book
        for sheet_name in gr_dfs.keys():
            gr_dfs[sheet_name].to_excel(writer, sheet_name=sheet_name)
            
        #writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        writer.save()
        messagebox.showinfo('Report generation', 'GR Report generated successfully')


    def letter_plots_all_1(self):
        conn = pymysql.connect(host='10.3.101.90', port=3306, user='sunil', passwd='ERLDC$cada123', db='amr_data')
        cur = conn.cursor()
        cur.execute("select feeder_name from master_mapping")
        lines = []
        for row in cur:
            lines.append(row[0])
        lines.sort()
        cur.close()
        conn.close()

        

        doc = SimpleDocTemplate("output/letters/Plots ({} to {}) VOL-I.pdf".format(
            self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')),
                                pagesize=letter,
                                rightMargin=40, leftMargin=20,
                                topMargin=50, bottomMargin=24)
        Story = []

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

        # Create return address

        for c in lines[0:150]:
            sem_to_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][c]
            scada_to_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][c]
            err_to = self.controller.frames[StartPage].df_res_to["Error in %"][c]
            sem_far_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][c]
            scada_far_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][c]
            err_far = self.controller.frames[StartPage].df_res_far["Error in %"][c]
            col_labels=['SEM','SCADA','Err']
            row_labels=['MU']
            table_vals_to = [[sem_to_mu, scada_to_mu, err_to]]
            table_vals_far = [[sem_far_mu, scada_far_mu, err_far]]
			
            fig_to, ax_to = plt.subplots()
            lns_to = []

            lns_to1 = ax_to.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'r', label='SEM', linewidth=1)
            lns_to.append(lns_to1)
            lns_to2 = ax_to.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
            lns_to.append(lns_to2)
            #ax2 = ax.twinx()
            #ax2.set_ylabel('Error in %', color='r')
            #ax2.tick_params(axis='y', labelcolor='r')
            #lns3 = ax2.plot(abs(self.controller.frames[StartPage].df_sem_scada1[c]), 'r', label='SCADA ERROR',linewidth=1)
            #lns.append(lns3)
            the_table_to = plt.table(cellText=table_vals_to,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
            the_table_to.set_fontsize = 12

            ax_to.set_title(c)
            ax_to.set_ylabel('Flow (in MW)')
            ax_to.set_xlabel('Timestamp')
            plt.gcf().autofmt_xdate()
            lns_to = lns_to[0] + lns_to[1]# + lns[2]
            labs_to = [l.get_label() for l in lns_to]
            leg_to = ax_to.legend(lns_to, labs_to, ncol=len(lns_to), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                            fancybox=True,
                            shadow=True)
            leg_to.get_frame().set_alpha(0.4)
            ax_to.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
            ax_to.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
            ax_to.minorticks_on()
            date_form_to = DateFormatter("%d %b %H:%M")
            ax_to.xaxis.set_major_formatter(date_form_to)
            plt.margins(0, 0)

            img_to = PdfImage(fig_to, width=600, height=320)
            plt.close(fig='all')
            Story.append(img_to)
            ######################## FAR END plot #############################
            fig, ax = plt.subplots()
            lns = []

            lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c]), 'r', label='SEM', linewidth=1)
            lns.append(lns1)
            lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c]), 'b', label='SCADA',
                           linewidth=1)
            lns.append(lns2)
            #ax2 = ax.twinx()
            #ax2.set_ylabel('Error in %', color='r')
            #ax2.tick_params(axis='y', labelcolor='r')
            #lns3 = ax2.plot(abs(self.controller.frames[StartPage].df_sem_scada2[c[:-8]]), 'r', label='SCADA ERROR',linewidth=1)
            #lns.append(lns3)
            the_table_far = plt.table(cellText=table_vals_far,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, fontsize=12, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
            the_table_far.set_fontsize = 12

            ax.set_title(c+" (other)")
            ax.set_ylabel('Flow (in MW)')
            ax.set_xlabel('Timestamp')
            plt.gcf().autofmt_xdate()
            lns = lns[0] + lns[1]# + lns[2]
            labs = [l.get_label() for l in lns]
            leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                            fancybox=True, shadow=True)
            leg.get_frame().set_alpha(0.4)
            ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
            ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
            ax.minorticks_on()
            date_form = DateFormatter("%d %b %H:%M")
            ax.xaxis.set_major_formatter(date_form)
            plt.margins(0, 0)

            img = PdfImage(fig, width=600, height=320)
            plt.close(fig='all')
            Story.append(img)
            # Story.append(Spacer(1, 24))
        doc.build(Story)
        messagebox.showinfo('Letter generation', 'Plots letter generated Successfully at output/letters')
        self.after(10000, self.letter_plots_all_2)

    def letter_plots_all_2(self):
        conn = pymysql.connect(host='10.3.101.90', port=3306, user='sunil', passwd='ERLDC$cada123', db='amr_data')
        cur = conn.cursor()
        cur.execute("select feeder_name from master_mapping")
        lines = []
        for row in cur:
            lines.append(row[0])
        lines.sort()
        cur.close()
        conn.close()

        

        doc = SimpleDocTemplate("output/letters/Plots ({} to {}) VOL-II.pdf".format(
            self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')),
                                pagesize=letter,
                                rightMargin=40, leftMargin=20,
                                topMargin=50, bottomMargin=24)
        Story = []

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

        # Create return address

        for c in lines[150:300]:
            sem_to_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][c]
            scada_to_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][c]
            err_to = self.controller.frames[StartPage].df_res_to["Error in %"][c]
            sem_far_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][c]
            scada_far_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][c]
            err_far = self.controller.frames[StartPage].df_res_far["Error in %"][c]
            col_labels=['SEM','SCADA','Err']
            row_labels=['MU']
            table_vals_to = [[sem_to_mu, scada_to_mu, err_to]]
            table_vals_far = [[sem_far_mu, scada_far_mu, err_far]]
			
            fig_to, ax_to = plt.subplots()
            lns_to = []

            lns_to1 = ax_to.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'r', label='SEM', linewidth=1)
            lns_to.append(lns_to1)
            lns_to2 = ax_to.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
            lns_to.append(lns_to2)
            #ax2 = ax.twinx()
            #ax2.set_ylabel('Error in %', color='r')
            #ax2.tick_params(axis='y', labelcolor='r')
            #lns3 = ax2.plot(abs(self.controller.frames[StartPage].df_sem_scada1[c]), 'r', label='SCADA ERROR',linewidth=1)
            #lns.append(lns3)
            the_table_to = plt.table(cellText=table_vals_to,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
            the_table_to.set_fontsize = 12

            ax_to.set_title(c)
            ax_to.set_ylabel('Flow (in MW)')
            ax_to.set_xlabel('Timestamp')
            plt.gcf().autofmt_xdate()
            lns_to = lns_to[0] + lns_to[1]# + lns[2]
            labs_to = [l.get_label() for l in lns_to]
            leg_to = ax_to.legend(lns_to, labs_to, ncol=len(lns_to), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                            fancybox=True,
                            shadow=True)
            leg_to.get_frame().set_alpha(0.4)
            ax_to.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
            ax_to.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
            ax_to.minorticks_on()
            date_form_to = DateFormatter("%d %b %H:%M")
            ax_to.xaxis.set_major_formatter(date_form_to)
            plt.margins(0, 0)

            img_to = PdfImage(fig_to, width=600, height=320)
            plt.close(fig='all')
            Story.append(img_to)
            ######################## FAR END plot #############################
            fig, ax = plt.subplots()
            lns = []

            lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c]), 'r', label='SEM', linewidth=1)
            lns.append(lns1)
            lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c]), 'b', label='SCADA',
                           linewidth=1)
            lns.append(lns2)
            #ax2 = ax.twinx()
            #ax2.set_ylabel('Error in %', color='r')
            #ax2.tick_params(axis='y', labelcolor='r')
            #lns3 = ax2.plot(abs(self.controller.frames[StartPage].df_sem_scada2[c[:-8]]), 'r', label='SCADA ERROR',linewidth=1)
            #lns.append(lns3)
            the_table_far = plt.table(cellText=table_vals_far,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, fontsize=12, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
            the_table_far.set_fontsize = 12

            ax.set_title(c+" (other)")
            ax.set_ylabel('Flow (in MW)')
            ax.set_xlabel('Timestamp')
            plt.gcf().autofmt_xdate()
            lns = lns[0] + lns[1]# + lns[2]
            labs = [l.get_label() for l in lns]
            leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                            fancybox=True, shadow=True)
            leg.get_frame().set_alpha(0.4)
            ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
            ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
            ax.minorticks_on()
            date_form = DateFormatter("%d %b %H:%M")
            ax.xaxis.set_major_formatter(date_form)
            plt.margins(0, 0)

            img = PdfImage(fig, width=600, height=320)
            plt.close(fig='all')
            Story.append(img)
            # Story.append(Spacer(1, 24))
        doc.build(Story)
        #messagebox.showinfo('Letter generation', 'Plots letter generated Successfully at output/letters')
        self.after(10000, self.letter_plots_all_3)

    def letter_plots_all_3(self):
        conn = pymysql.connect(host='10.3.101.90', port=3306, user='sunil', passwd='ERLDC$cada123', db='amr_data')
        cur = conn.cursor()
        cur.execute("select feeder_name from master_mapping")
        lines = []
        for row in cur:
            lines.append(row[0])
        lines.sort()
        cur.close()
        conn.close()

        

        doc = SimpleDocTemplate("output/letters/Plots ({} to {}) VOL-III.pdf".format(
            self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y'),
            self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')),
                                pagesize=letter,
                                rightMargin=40, leftMargin=20,
                                topMargin=50, bottomMargin=24)
        Story = []

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

        # Create return address

        for c in lines[300:]:
            sem_to_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][c]
            scada_to_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][c]
            err_to = self.controller.frames[StartPage].df_res_to["Error in %"][c]
            sem_far_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][c]
            scada_far_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][c]
            err_far = self.controller.frames[StartPage].df_res_far["Error in %"][c]
            col_labels=['SEM','SCADA','Err']
            row_labels=['MU']
            table_vals_to = [[sem_to_mu, scada_to_mu, err_to]]
            table_vals_far = [[sem_far_mu, scada_far_mu, err_far]]
			
            fig_to, ax_to = plt.subplots()
            lns_to = []

            lns_to1 = ax_to.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), '#a86632', label='SEM', linewidth=1)
            lns_to.append(lns_to1)
            lns_to2 = ax_to.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
            lns_to.append(lns_to2)
            #ax2 = ax.twinx()
            #ax2.set_ylabel('Error in %', color='r')
            #ax2.tick_params(axis='y', labelcolor='r')
            #lns3 = ax2.plot(abs(self.controller.frames[StartPage].df_sem_scada1[c]), 'r', label='SCADA ERROR',linewidth=1)
            #lns.append(lns3)
            the_table_to = plt.table(cellText=table_vals_to,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
            the_table_to.set_fontsize = 12

            ax_to.set_title(c)
            ax_to.set_ylabel('Flow (in MW)')
            ax_to.set_xlabel('Timestamp')
            plt.gcf().autofmt_xdate()
            lns_to = lns_to[0] + lns_to[1]# + lns[2]
            labs_to = [l.get_label() for l in lns_to]
            leg_to = ax_to.legend(lns_to, labs_to, ncol=len(lns_to), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                            fancybox=True,
                            shadow=True)
            leg_to.get_frame().set_alpha(0.4)
            ax_to.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
            ax_to.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
            ax_to.minorticks_on()
            date_form_to = DateFormatter("%d %b %H:%M")
            ax_to.xaxis.set_major_formatter(date_form_to)
            plt.margins(0, 0)

            img_to = PdfImage(fig_to, width=600, height=320)
            plt.close(fig='all')
            Story.append(img_to)
            ######################## FAR END plot #############################
            fig, ax = plt.subplots()
            lns = []

            lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c]), '#a86632', label='SEM', linewidth=1)
            lns.append(lns1)
            lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c]), 'b', label='SCADA',
                           linewidth=1)
            lns.append(lns2)
            #ax2 = ax.twinx()
            #ax2.set_ylabel('Error in %', color='r')
            #ax2.tick_params(axis='y', labelcolor='r')
            #lns3 = ax2.plot(abs(self.controller.frames[StartPage].df_sem_scada2[c[:-8]]), 'r', label='SCADA ERROR',linewidth=1)
            #lns.append(lns3)
            the_table_far = plt.table(cellText=table_vals_far,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, fontsize=12, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
            the_table_far.set_fontsize = 12

            ax.set_title(c+" (other)")
            ax.set_ylabel('Flow (in MW)')
            ax.set_xlabel('Timestamp')
            plt.gcf().autofmt_xdate()
            lns = lns[0] + lns[1]# + lns[2]
            labs = [l.get_label() for l in lns]
            leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),
                            fancybox=True, shadow=True)
            leg.get_frame().set_alpha(0.4)
            ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
            ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
            ax.minorticks_on()
            date_form = DateFormatter("%d %b %H:%M")
            ax.xaxis.set_major_formatter(date_form)
            plt.margins(0, 0)

            img = PdfImage(fig, width=600, height=320)
            plt.close(fig='all')
            Story.append(img)
            # Story.append(Spacer(1, 24))
        doc.build(Story)
        messagebox.showinfo('Letter generation', 'Plots letter generated Successfully at output/letters')

    def letter_bh_jh_dv_plots(self):
        start_dt = self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y')
        end_dt = self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')
        month_folder = self.controller.frames[StartPage].cal_start.get_date().strftime('%b %y')
        year_folder = self.controller.frames[StartPage].cal_start.get_date().strftime('%Y')
        try:
            os.makedirs('output/letters/{}'.format(year_folder))
        except FileExistsError:
            pass        # directory already exists

        try:
            os.makedirs('output/letters/{}/{}'.format(year_folder, month_folder))
        except FileExistsError:
            pass        # directory already exists

        try:
            os.makedirs('output/letters/{}/{}/{}_to_{}'.format(year_folder, month_folder, start_dt, end_dt))
        except FileExistsError:
            pass
        
        const_dict1 = {'BH': ['BH', '4'], 'JH': ['JH', '5'], 'DV': ['DV', '2']}
        msg_str = "Plot files: "
        for state_name in const_dict1:
            print(state_name)
            conn = pymysql.connect(host='10.3.101.90', port=3306, user='sunil', passwd='ERLDC$cada123', db='amr_data')
            cur = conn.cursor()
            cur.execute("select feeder_name, To_Plot, Far_Plot, to_remark, far_remark from plot_mapping where feeder_from='{}' or to_feeder='{}'".format(state_name, state_name))
            lines = {}
            for row in cur:
                lines[row[0]] = [row[1]]
                #lines[row[0]].append(row[1])
                lines[row[0]].append(row[2])
                lines[row[0]].append(row[3])
                lines[row[0]].append(row[4])
            #lines.sort()
            ordered_lines = collections.OrderedDict(sorted(lines.items(), reverse=True))
            #print(ordered_lines)
            cur.close()
            conn.close()

        

            doc = SimpleDocTemplate("output/letters/{}/{}/{}_to_{}/Section {} Plots {}.pdf".format(year_folder, month_folder, start_dt, end_dt, const_dict1[state_name][1], const_dict1[state_name][0]),pagesize=letter,rightMargin=45, leftMargin=15,topMargin=50, bottomMargin=24)
            Story = []

            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
            styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
            styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
            styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

            # Create return address

            for c in ordered_lines:
                sem_to_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][c]
                scada_to_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][c]
                err_to = self.controller.frames[StartPage].df_res_to["Error in %"][c]
                sem_far_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][c]
                scada_far_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][c]
                err_far = self.controller.frames[StartPage].df_res_far["Error in %"][c]
                col_labels=['SEM','SCADA','% Err']
                row_labels=['MU']
                table_vals_to = [[sem_to_mu, scada_to_mu, err_to]]
                table_vals_far = [[sem_far_mu, scada_far_mu, err_far]]

                if ordered_lines[c][0]=='Yes':
                    fig_to, ax_to = plt.subplots()
                    lns_to = []

                    lns_to1 = ax_to.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'r', label='SEM', linewidth=1)
                    lns_to.append(lns_to1)
                    lns_to2 = ax_to.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
                    lns_to.append(lns_to2)
                    #######was commented##############
                    ax2_to = ax_to.twinx()
                    ax2_to.set_ylabel('Error in %', color='green')
                    ax2_to.tick_params(axis='y', labelcolor='green')
                    lns_to3 = ax2_to.fill_between(self.controller.frames[StartPage].dff_sem_scada_to[c].index, abs(self.controller.frames[StartPage].dff_sem_scada_to[c]), color='green', alpha=0.7, label='SCADA ERROR',linewidth=1)
                    lns_to.append(lns_to3)
                    ax2_to.set_ylim(0,150)
                    #########was commented##############
                    the_table_to = plt.table(cellText=table_vals_to,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                    the_table_to.set_fontsize = 12
                    if ordered_lines[c][2] != None:
                        rmk_txt_to = plt.table(cellText=[['Remark: '+ordered_lines[c][2]]], bbox= [-0.165, -0.3,0.45,0.085], fontsize=3, cellLoc='left', edges='open')

                    ax_to.set_title(c)
                    ax_to.set_ylabel('Flow (in MW)')
                    ax_to.set_xlabel('Timestamp')
                    plt.gcf().autofmt_xdate()
                    lns_to = lns_to[0] + lns_to[1]# + lns[2]
                    labs_to = [l.get_label() for l in lns_to]
                    leg_to = ax_to.legend(lns_to, labs_to, ncol=len(lns_to), loc='upper center', bbox_to_anchor=(0.5, -0.18),fancybox=True, shadow=True)
                    leg_to.get_frame().set_alpha(0.4)
                    ax_to.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                    ax_to.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                    ax_to.minorticks_on()
                    date_form_to = DateFormatter("%d %b %H:%M")
                    ax_to.xaxis.set_major_formatter(date_form_to)
                    plt.margins(0, 0)
                    fig_to.tight_layout()

                    img_to = PdfImage(fig_to, width=600, height=320)
                    plt.close(fig='all')
                    fig_to.clear()
                    plt.close(fig_to)
                    Story.append(img_to)
                ######################## FAR END plot #############################
                if ordered_lines[c][1]=='Yes':
                    fig, ax = plt.subplots()
                    lns = []

                    lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c]), 'r', label='SEM', linewidth=1)
                    lns.append(lns1)
                    lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c]), 'b', label='SCADA',linewidth=1)
                    lns.append(lns2)
                    ax2_far = ax.twinx()
                    ax2_far.set_ylabel('Error in %', color='green')
                    ax2_far.tick_params(axis='y', labelcolor='green')
                    lns3 = ax2_far.fill_between(self.controller.frames[StartPage].dff_sem_scada_far[c].index, abs(self.controller.frames[StartPage].dff_sem_scada_far[c]), color='green', alpha=0.7, label='SCADA ERROR',linewidth=1)
                    lns.append(lns3)
                    ax2_far.set_ylim(0,150)
                    the_table_far = plt.table(cellText=table_vals_far,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, fontsize=12, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                    the_table_far.set_fontsize = 12
                    if ordered_lines[c][3] != None:
                        rmk_txt_far = plt.table(cellText=[['Remark: '+ordered_lines[c][3]]], bbox= [-0.165, -0.3,0.45,0.085], fontsize=3, cellLoc='left', edges='open')

                    ax.set_title(rev_line_name(c))
                    #ax.set_title(c+" (other)")
                    ax.set_ylabel('Flow (in MW)')
                    ax.set_xlabel('Timestamp')
                    plt.gcf().autofmt_xdate()
                    lns = lns[0] + lns[1]# + lns[2]
                    labs = [l.get_label() for l in lns]
                    leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),fancybox=True, shadow=True)
                    leg.get_frame().set_alpha(0.4)
                    ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                    ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                    ax.minorticks_on()
                    date_form = DateFormatter("%d %b %H:%M")
                    ax.xaxis.set_major_formatter(date_form)
                    plt.margins(0, 0)
                    fig.tight_layout()

                    img = PdfImage(fig, width=600, height=320)
                    plt.close(fig='all')
                    fig.clear()
                    plt.close(fig)
                    Story.append(img)
                # Story.append(Spacer(1, 24))
            doc.build(Story)
            msg_str = msg_str + ", " + state_name
            print(state_name)
        
        #messagebox.showinfo('Letter generation', msg_str)
        self.after(10000, self.letter_wb_gr_si_reg_plots)
        self.after(10000, self.ir_plots)
        self.after(10000, self.summary_pages)
        #print("report completed")

    def letter_wb_gr_si_reg_plots(self):
        start_dt = self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y')
        end_dt = self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')
        month_folder = self.controller.frames[StartPage].cal_start.get_date().strftime('%b %y')
        year_folder = self.controller.frames[StartPage].cal_start.get_date().strftime('%Y')
        try:
            os.makedirs('output/letters/{}'.format(year_folder))
        except FileExistsError:
            pass        # directory already exists

        try:
            os.makedirs('output/letters/{}/{}'.format(year_folder, month_folder))
        except FileExistsError:
            pass        # directory already exists

        try:
            os.makedirs('output/letters/{}/{}/{}_to_{}'.format(year_folder, month_folder, start_dt, end_dt))
        except FileExistsError:
            pass
        
        const_dict = {'WB':['WB', '6'] , 'GR': ['GR','3'], 'SI': ['SI', '7'], 'MIS_CALC_TO': ['Regional','1']}
        msg_str = "Plot files: "
        for state_name in const_dict:
            print(state_name)
            conn = pymysql.connect(host='10.3.101.90', port=3306, user='sunil', passwd='ERLDC$cada123', db='amr_data')
            cur = conn.cursor()
            cur.execute("select feeder_name, To_Plot, Far_Plot, to_remark, far_remark from plot_mapping where feeder_from='{}' or to_feeder='{}'".format(state_name, state_name))
            lines = {}
            for row in cur:
                lines[row[0]] = [row[1]]
                #lines[row[0]].append(row[1])
                lines[row[0]].append(row[2])
                lines[row[0]].append(row[3])
                lines[row[0]].append(row[4])
            #lines.sort()
            ordered_lines = collections.OrderedDict(sorted(lines.items(), reverse=True))
            #print(ordered_lines)
            cur.close()
            conn.close()

        

            doc = SimpleDocTemplate("output/letters/{}/{}/{}_to_{}/Section {} Plots {}.pdf".format(year_folder, month_folder, start_dt, end_dt, const_dict[state_name][1], const_dict[state_name][0]),pagesize=letter,rightMargin=45, leftMargin=15,topMargin=50, bottomMargin=24)
            Story = []

            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
            styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
            styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
            styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

            # Create return address

            for c in ordered_lines:
                sem_to_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][c]
                scada_to_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][c]
                err_to = self.controller.frames[StartPage].df_res_to["Error in %"][c]
                sem_far_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][c]
                scada_far_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][c]
                err_far = self.controller.frames[StartPage].df_res_far["Error in %"][c]
                col_labels=['SEM','SCADA','% Err']
                row_labels=['MU']
                table_vals_to = [[sem_to_mu, scada_to_mu, err_to]]
                table_vals_far = [[sem_far_mu, scada_far_mu, err_far]]

                if ordered_lines[c][0]=='Yes':
                    fig_to, ax_to = plt.subplots()
                    lns_to = []

                    lns_to1 = ax_to.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'r', label='SEM', linewidth=1)
                    lns_to.append(lns_to1)
                    lns_to2 = ax_to.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
                    lns_to.append(lns_to2)
                    #######was commented##############
                    ax2_to = ax_to.twinx()
                    ax2_to.set_ylabel('Error in %', color='green')
                    ax2_to.tick_params(axis='y', labelcolor='green')
                    lns_to3 = ax2_to.fill_between(self.controller.frames[StartPage].dff_sem_scada_to[c].index, abs(self.controller.frames[StartPage].dff_sem_scada_to[c]), color='green', alpha=0.7, label='SCADA ERROR',linewidth=1)
                    lns_to.append(lns_to3)
                    ax2_to.set_ylim(0,150)
                    #########was commented##############
                    the_table_to = plt.table(cellText=table_vals_to,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                    the_table_to.set_fontsize = 12
                    if ordered_lines[c][2] != None:
                        rmk_txt_to = plt.table(cellText=[['Remark: '+ordered_lines[c][2]]], bbox= [-0.165, -0.3,0.45,0.085], fontsize=3, cellLoc='left', edges='open')

                    ax_to.set_title(c)
                    ax_to.set_ylabel('Flow (in MW)')
                    ax_to.set_xlabel('Timestamp')
                    plt.gcf().autofmt_xdate()
                    lns_to = lns_to[0] + lns_to[1]# + lns[2]
                    labs_to = [l.get_label() for l in lns_to]
                    leg_to = ax_to.legend(lns_to, labs_to, ncol=len(lns_to), loc='upper center', bbox_to_anchor=(0.5, -0.18),fancybox=True, shadow=True)
                    leg_to.get_frame().set_alpha(0.4)
                    ax_to.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                    ax_to.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                    ax_to.minorticks_on()
                    date_form_to = DateFormatter("%d %b %H:%M")
                    ax_to.xaxis.set_major_formatter(date_form_to)
                    plt.margins(0, 0)
                    fig_to.tight_layout()

                    img_to = PdfImage(fig_to, width=600, height=320)
                    plt.close(fig='all')
                    fig_to.clear()
                    plt.close(fig_to)
                    Story.append(img_to)
                ######################## FAR END plot #############################
                if ordered_lines[c][1]=='Yes':
                    fig, ax = plt.subplots()
                    lns = []

                    lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c]), 'r', label='SEM', linewidth=1)
                    lns.append(lns1)
                    lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c]), 'b', label='SCADA',linewidth=1)
                    lns.append(lns2)
                    ax2_far = ax.twinx()
                    ax2_far.set_ylabel('Error in %', color='green')
                    ax2_far.tick_params(axis='y', labelcolor='green')
                    lns3 = ax2_far.fill_between(self.controller.frames[StartPage].dff_sem_scada_far[c].index, abs(self.controller.frames[StartPage].dff_sem_scada_far[c]), color='green', alpha=0.7, label='SCADA ERROR',linewidth=1)
                    lns.append(lns3)
                    ax2_far.set_ylim(0,150)
                    the_table_far = plt.table(cellText=table_vals_far,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, fontsize=12, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                    the_table_far.set_fontsize = 12
                    if ordered_lines[c][3] != None:
                        rmk_txt_far = plt.table(cellText=[['Remark: '+ordered_lines[c][3]]], bbox= [-0.165, -0.3,0.45,0.085], fontsize=3, cellLoc='left', edges='open')

                    ax.set_title(rev_line_name(c))
                    #ax.set_title(c+" (other)")
                    ax.set_ylabel('Flow (in MW)')
                    ax.set_xlabel('Timestamp')
                    plt.gcf().autofmt_xdate()
                    lns = lns[0] + lns[1]# + lns[2]
                    labs = [l.get_label() for l in lns]
                    leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),fancybox=True, shadow=True)
                    leg.get_frame().set_alpha(0.4)
                    ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                    ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                    ax.minorticks_on()
                    date_form = DateFormatter("%d %b %H:%M")
                    ax.xaxis.set_major_formatter(date_form)
                    plt.margins(0, 0)
                    fig.tight_layout()

                    img = PdfImage(fig, width=600, height=320)
                    plt.close(fig='all')
                    fig.clear()
                    plt.close(fig)
                    Story.append(img)
                # Story.append(Spacer(1, 24))
            doc.build(Story)
            msg_str = msg_str + ", " + state_name
            print(state_name)
        
        #messagebox.showinfo('Letter generation', msg_str)
        #self.after(10000, self.ir_plots)
	
    def ir_plots(self):
        start_dt = self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y')
        end_dt = self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')
        month_folder = self.controller.frames[StartPage].cal_start.get_date().strftime('%b %y')
        year_folder = self.controller.frames[StartPage].cal_start.get_date().strftime('%Y')
        try:
            os.makedirs('output/letters/{}'.format(year_folder))
        except FileExistsError:
            pass        # directory already exists

        try:
            os.makedirs('output/letters/{}/{}'.format(year_folder, month_folder))
        except FileExistsError:
            pass        # directory already exists

        try:
            os.makedirs('output/letters/{}/{}/{}_to_{}'.format(year_folder, month_folder, start_dt, end_dt))
        except FileExistsError:
            pass
        
        IR_dict = {"(NR)":['ER-NR', '11'], "(WR)": ['ER-WR', '8'], "(SR)": ['ER-SR', '9'], "(NE)": ['ER-NER', '10'], "(NEPAL)": ['NEPAL', '12'], "(B''DESH)": ['Bangladesh', '12']}
        msg_str = "IR Plots: "
        for rgn_name in IR_dict:
            print(rgn_name)
            conn = pymysql.connect(host='10.3.101.90', port=3306, user='sunil', passwd='ERLDC$cada123', db='amr_data')
            cur = conn.cursor()
            cur.execute("select feeder_name, To_Plot, Far_Plot, to_remark, far_remark from plot_mapping where feeder_name like '%{}%'".format(rgn_name))
            lines = {}
            for row in cur:
                lines[row[0]] = [row[1]]
                #lines[row[0]].append(row[1])
                lines[row[0]].append(row[2])
                lines[row[0]].append(row[3])
                lines[row[0]].append(row[4])
            #lines.sort()
            ordered_lines = collections.OrderedDict(sorted(lines.items(), reverse=True))
            #print(ordered_lines)
            cur.close()
            conn.close()

        

            doc = SimpleDocTemplate("output/letters/{}/{}/{}_to_{}/Section {} Plots {}.pdf".format(year_folder, month_folder, start_dt, end_dt, IR_dict[rgn_name][1], IR_dict[rgn_name][0]),pagesize=letter,rightMargin=50, leftMargin=10,topMargin=50, bottomMargin=24)
            Story = []

            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
            styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
            styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
            styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

            # Create return address

            for c in ordered_lines:
                sem_to_mu = self.controller.frames[StartPage].df_res_to["SEM MU"][c]
                scada_to_mu = self.controller.frames[StartPage].df_res_to["SCADA MU"][c]
                err_to = self.controller.frames[StartPage].df_res_to["Error in %"][c]
                sem_far_mu = self.controller.frames[StartPage].df_res_far["SEM MU"][c]
                scada_far_mu = self.controller.frames[StartPage].df_res_far["SCADA MU"][c]
                err_far = self.controller.frames[StartPage].df_res_far["Error in %"][c]
                col_labels=['SEM','SCADA','Err']
                row_labels=['MU']
                table_vals_to = [[sem_to_mu, scada_to_mu, err_to]]
                table_vals_far = [[sem_far_mu, scada_far_mu, err_far]]

                if ordered_lines[c][0]=='Yes':
                    fig_to, ax_to = plt.subplots()
                    lns_to = []

                    lns_to1 = ax_to.plot(abs(self.controller.frames[StartPage].dff_sem_to_end[c]), 'r', label='SEM', linewidth=1)
                    lns_to.append(lns_to1)
                    lns_to2 = ax_to.plot(abs(self.controller.frames[StartPage].dff_scada_to_end[c]), 'b', label='SCADA', linewidth=1)
                    lns_to.append(lns_to2)
                    #######was commented##############
                    ax2_to = ax_to.twinx()
                    ax2_to.set_ylabel('Error in %', color='green')
                    ax2_to.tick_params(axis='y', labelcolor='green')
                    lns_to3 = ax2_to.fill_between(self.controller.frames[StartPage].dff_sem_scada_to[c].index, abs(self.controller.frames[StartPage].dff_sem_scada_to[c]), color='green', alpha=0.7, label='SCADA ERROR',linewidth=1)
                    lns_to.append(lns_to3)
                    ax2_to.set_ylim(0,150)
                    #########was commented##############
                    the_table_to = plt.table(cellText=table_vals_to,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                    the_table_to.set_fontsize = 12
                    if ordered_lines[c][2] != None:
                        the_table_to_rmk = plt.table(cellText=[['Remark: '+ordered_lines[c][2]]], bbox= [-0.165, -0.3,0.45,0.085], fontsize=3, cellLoc='left', edges='open')

                    ax_to.set_title(c)
                    ax_to.set_ylabel('Flow (in MW)')
                    ax_to.set_xlabel('Timestamp')
                    plt.gcf().autofmt_xdate()
                    lns_to = lns_to[0] + lns_to[1]# + lns[2]
                    labs_to = [l.get_label() for l in lns_to]
                    leg_to = ax_to.legend(lns_to, labs_to, ncol=len(lns_to), loc='upper center', bbox_to_anchor=(0.5, -0.18),fancybox=True, shadow=True)
                    leg_to.get_frame().set_alpha(0.4)
                    ax_to.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                    ax_to.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                    ax_to.minorticks_on()
                    date_form_to = DateFormatter("%d %b %H:%M")
                    ax_to.xaxis.set_major_formatter(date_form_to)
                    plt.margins(0, 0)
                    fig_to.tight_layout()

                    img_to = PdfImage(fig_to, width=600, height=320)
                    plt.close(fig='all')
                    fig_to.clear()
                    plt.close(fig_to)
                    Story.append(img_to)
                ######################## FAR END plot #############################
                if ordered_lines[c][1]=='Yes':
                    fig, ax = plt.subplots()
                    lns = []

                    lns1 = ax.plot(abs(self.controller.frames[StartPage].dff_sem_far_end[c]), 'r', label='SEM', linewidth=1)
                    lns.append(lns1)
                    lns2 = ax.plot(abs(self.controller.frames[StartPage].dff_scada_far_end[c]), 'b', label='SCADA',linewidth=1)
                    lns.append(lns2)
                    ax2_far = ax.twinx()
                    ax2_far.set_ylabel('Error in %', color='green')
                    ax2_far.tick_params(axis='y', labelcolor='green')
                    lns3 = ax2_far.fill_between(self.controller.frames[StartPage].dff_sem_scada_far[c].index, abs(self.controller.frames[StartPage].dff_sem_scada_far[c]), color='green', alpha=0.7, label='SCADA ERROR',linewidth=1)
                    lns.append(lns3)
                    ax2_far.set_ylim(0,150)
                    the_table_far = plt.table(cellText=table_vals_far,colWidths = [0.1]*3,rowLabels=row_labels,colLabels=col_labels, fontsize=12, loc='top left', bbox=[0.75,-0.28,0.3,0.13])
                    the_table_far.set_fontsize = 12
                    if ordered_lines[c][3] != None:
                        the_table_far_text = plt.table(cellText=[['Remark: '+ordered_lines[c][3]]], bbox= [-0.165, -0.3,0.45,0.085], fontsize=3, cellLoc='left', edges='open')

                    ax.set_title(rev_line_name(c))
                    #ax.set_title(c+" (other)")
                    ax.set_ylabel('Flow (in MW)')
                    ax.set_xlabel('Timestamp')
                    plt.gcf().autofmt_xdate()
                    lns = lns[0] + lns[1]# + lns[2]
                    labs = [l.get_label() for l in lns]
                    leg = ax.legend(lns, labs, ncol=len(lns), loc='upper center', bbox_to_anchor=(0.5, -0.18),fancybox=True, shadow=True)
                    leg.get_frame().set_alpha(0.4)
                    ax.grid(which='major', linestyle='-', linewidth='0.5', color='black', alpha=0.6)
                    ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black', alpha=0.4)
                    ax.minorticks_on()
                    date_form = DateFormatter("%d %b %H:%M")
                    ax.xaxis.set_major_formatter(date_form)
                    plt.margins(0, 0)
                    fig.tight_layout()

                    img = PdfImage(fig, width=600, height=320)
                    plt.close(fig='all')
                    fig.clear()
                    plt.close(fig)
                    Story.append(img)
                # Story.append(Spacer(1, 24))
            doc.build(Story)
            msg_str = msg_str + ", " + rgn_name
            print(rgn_name)
        #messagebox.showinfo('Letter generation', msg_str)
        #self.after(10000, self.summary_pages)

    def summary_pages(self):
        start_dt = self.controller.frames[StartPage].cal_start.get_date().strftime('%d-%m-%Y')
        end_dt = self.controller.frames[StartPage].cal_end.get_date().strftime('%d-%m-%Y')
        month_folder = self.controller.frames[StartPage].cal_start.get_date().strftime('%b %y')
        year_folder = self.controller.frames[StartPage].cal_start.get_date().strftime('%Y')
        try:
            os.makedirs('output/letters/{}'.format(year_folder))
        except FileExistsError:
            pass        # directory already exists

        try:
            os.makedirs('output/letters/{}/{}'.format(year_folder, month_folder))
        except FileExistsError:
            pass        # directory already exists

        try:
            os.makedirs('output/letters/{}/{}/{}_to_{}'.format(year_folder, month_folder, start_dt, end_dt))
        except FileExistsError:
            pass
        
        sum_dict_states = {"MIS_CALC_TO": [" Eastern Regional Utilities", "1"], "DV": ["DVC", "2"], "GR": ["OPTCL", "3"],"BH": ["Bihar", '4'], "JH": ["Jharkhand", '5'], "WB": ["WBSETCL", "6"], "SI": ["Sikkim", "7"]}
        for state in sum_dict_states:
            conn = pymysql.connect(host='10.3.101.90', port=3306, user='sunil', passwd='ERLDC$cada123', db='amr_data')
            cur = conn.cursor()
            cur.execute("select feeder_name from plot_mapping where feeder_from='{}' or to_feeder='{}'".format(state, state))
            lines = []
            for row in cur:
                lines.append(row[0])
            lines = sorted(lines, reverse=True)
            cur.close()
            conn.close()

        

            doc = SimpleDocTemplate("output/letters/{}/{}/{}_to_{}/Section {} {}.pdf".format(year_folder, month_folder, start_dt, end_dt, str(sum_dict_states[state][1]), state),pagesize=letter,rightMargin=50, leftMargin=30,topMargin=50, bottomMargin=24)
            Story = []
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Normal_CENTER', parent=styles['Normal'],fontName='Helvetica',wordWrap='LTR',alignment=TA_CENTER,fontSize=12,leading=13, textColor=colors.black, borderPadding=0, leftIndent=0, rightIndent=0, spaceAfter=0, spaceBefore=0, splitLongWords=True, spaceShrinkage=0.05,))
            Story.append(Paragraph("Section " + sum_dict_states[state][1], styles['Title']))
            Story.append(Paragraph("SCADA vs SEM data comparison of " + sum_dict_states[state][0] + " tie lines", styles['Title']))
            Story.append(Paragraph("To End Differences (values in MU)", styles['Normal_CENTER']))

            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
            styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
            styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
            styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

            df_sem = self.controller.frames[StartPage].dff_sem_to_end[lines]
            df_scada = self.controller.frames[StartPage].dff_scada_to_end[lines]
            df_mu = df_sem.groupby(df_sem.index.date).mean()*0.024 - df_scada.groupby(df_scada.index.date).mean()*0.024
            df_mu = df_mu.round(1)
            df_mu.index = pd.to_datetime(df_mu.index, format = '%Y-%m-%d').strftime('%d-%m-%Y')
            df_mu = df_mu.transpose()
            df_mu.index.name = "List of Feeders for " + sum_dict_states[state][0]
            df_mu = df_mu.reset_index()
            df_mu.insert(0, 'Sl No', range(1, 1 + len(df_mu)))

            lista = [df_mu.columns[:,].values.astype(str).tolist()] + df_mu.values.tolist()
            #lista[0][1] = verticalText(lista[0][1])


            data_len = len(lista)
            
            ts = [('ALIGN', (1,1), (-1,-1), 'CENTER'),
                  ('ROTATE',(0,0), (0,-1), 90),
                  ('VALIGN',(1,0), (1,-1), 'MIDDLE'),
                  ('GRID',(0,0),(-1,-1),0.5,colors.black),
                  ('LINEABOVE', (0,0), (-1,0), 1, colors.purple),
                  ('LINEBELOW', (0,0), (-1,0), 1, colors.purple),
                  ('FONTSIZE', (0,0), (-1,-1), 6),
                  ('FONT', (0,0), (-1,0), 'Times-Bold'),
                  ('BACKGROUND', (0,0), (-1,0), 'lightblue'),
                  ('FONT', (0,0), (1,-1), 'Times-Bold')]
                  #('LINEABOVE', (0,-1), (-1,-1), 1, colors.purple),
                  #('LINEBELOW', (0,-1), (-1,-1), 0.5, colors.purple, 1, None, None, 4,1),
                  #('LINEBELOW', (0,-1), (-1,-1), 1, colors.red),
                  #('FONT', (0,-1), (-1,-1), 'Times-Bold'),
                  #('BACKGROUND',(1,1),(-2,-2),colors.green),
                  #('TEXTCOLOR',(0,0),(0,-1),colors.red)]
##            

            table = Table(lista, repeatRows=1, style=ts)
            for each in range(data_len):
                if each % 2 == 0:
                    bg_color = colors.whitesmoke
                else:
                    bg_color = colors.lightgrey

                table.setStyle(TableStyle([('BACKGROUND', (0, each), (-1, each), bg_color)]))
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightblue)]))

            for row, values, in enumerate(lista):
                for column, value in enumerate(values):
                    if (row>0 and column>1) and (int(value) < -0.5 or int(value) > 0.5):
                        table.setStyle(TableStyle([('BACKGROUND', (column, row), (column, row), colors.red)]))
            Story.append(table)

           
            doc.build(Story)
        
        #======================= IR summery pages ==============================================================================================================================================================================
        sum_dict_IR = {"(WR)": ["ER-WR", "8"], "(SR)": ["ER-SR", "9"], "(NE)": ["ER-NER", '10'], "(NR)": ["ER-NR", '11'], "(B''DESH)": ["Transnational-Bangladesh", '12'], "(NEPAL)": ["Transnational-Nepal", "12"],}
        for rgn_name in sum_dict_IR:
            conn = pymysql.connect(host='10.3.101.90', port=3306, user='sunil', passwd='ERLDC$cada123', db='amr_data')
            cur = conn.cursor()
            cur.execute("select feeder_name from plot_mapping where feeder_name like '%{}%'".format(rgn_name))
            lines = []
            for row in cur:
                lines.append(row[0])
            lines = sorted(lines, reverse=True)
            cur.close()
            conn.close()

        

            doc = SimpleDocTemplate("output/letters/{}/{}/{}_to_{}/Section {} {}.pdf".format(year_folder, month_folder, start_dt, end_dt, str(sum_dict_IR[rgn_name][1]), rgn_name),pagesize=letter,rightMargin=50, leftMargin=30,topMargin=50, bottomMargin=24)
            Story = []
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Normal_CENTER', parent=styles['Normal'],fontName='Helvetica',wordWrap='LTR',alignment=TA_CENTER,fontSize=12,leading=13, textColor=colors.black, borderPadding=0, leftIndent=0, rightIndent=0, spaceAfter=0, spaceBefore=0, splitLongWords=True, spaceShrinkage=0.05,))
            Story.append(Paragraph("Section " + sum_dict_IR[rgn_name][1], styles['Title']))
            Story.append(Paragraph("SCADA vs SEM data comparison of " + sum_dict_IR[rgn_name][0] + " tie lines", styles['Title']))
            Story.append(Paragraph("To End Differences (values in MU)", styles['Normal_CENTER']))

            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
            styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
            styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
            styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

            df_sem = self.controller.frames[StartPage].dff_sem_to_end[lines]
            df_scada = self.controller.frames[StartPage].dff_scada_to_end[lines]
            df_mu = df_sem.groupby(df_sem.index.date).mean()*0.024 - df_scada.groupby(df_scada.index.date).mean()*0.024
            df_mu = df_mu.round(1)
            df_mu.index = pd.to_datetime(df_mu.index, format = '%Y-%m-%d').strftime('%d-%m-%Y')
            df_mu = df_mu.transpose()
            df_mu.index.name = "List of Feeders for " + sum_dict_IR[rgn_name][0]
            df_mu = df_mu.reset_index()
            df_mu.insert(0, 'Sl No', range(1, 1 + len(df_mu)))

            lista = [df_mu.columns[:,].values.astype(str).tolist()] + df_mu.values.tolist()

            data_len = len(lista)
            
            ts = [('ALIGN', (1,1), (-1,-1), 'CENTER'),
                  ('ROTATE',(0,0), (0,-1), 90),
                  ('VALIGN',(1,0), (1,-1), 'MIDDLE'),
                  ('GRID',(0,0),(-1,-1),0.5,colors.black),
                  ('LINEABOVE', (0,0), (-1,0), 1, colors.purple),
                  ('LINEBELOW', (0,0), (-1,0), 1, colors.purple),
                  ('FONTSIZE', (0,0), (-1,-1), 6),
                  ('FONT', (0,0), (-1,0), 'Times-Bold'),
                  ('BACKGROUND', (0,0), (-1,0), 'lightblue'),
                  ('FONT', (0,0), (1,-1), 'Times-Bold')]
                  

            table = Table(lista, repeatRows=1, style=ts)
            for each in range(data_len):
                if each % 2 == 0:
                    bg_color = colors.whitesmoke
                else:
                    bg_color = colors.lightgrey

                table.setStyle(TableStyle([('BACKGROUND', (0, each), (-1, each), bg_color)]))
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightblue)]))

            for row, values, in enumerate(lista):
                for column, value in enumerate(values):
                    if (row>0 and column>1) and (int(value) < -0.5 or int(value) > 0.5):
                        table.setStyle(TableStyle([('BACKGROUND', (column, row), (column, row), colors.red)]))
            Story.append(table)

           
            doc.build(Story)

        pdfs = ["output/Index Page.pdf",
                "output/letters/{}/{}/{}_to_{}/Section 1 MIS_CALC_TO.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 1 Plots Regional.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 2 DV.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 2 Plots DV.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 3 GR.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 3 Plots GR.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 4 BH.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 4 Plots BH.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 5 JH.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 5 Plots JH.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 6 WB.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 6 Plots WB.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 7 SI.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 7 Plots SI.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 8 (WR).pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 8 Plots ER-WR.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 9 (SR).pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 9 Plots ER-SR.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 10 (NE).pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 10 Plots ER-NER.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 11 (NR).pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 11 Plots ER-NR.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 12 (B''DESH).pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 12 (NEPAL).pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 12 Plots Bangladesh.pdf".format(year_folder, month_folder, start_dt, end_dt),
                "output/letters/{}/{}/{}_to_{}/Section 12 Plots NEPAL.pdf".format(year_folder, month_folder, start_dt, end_dt)]

        merger = PdfFileMerger()

        for pdf in pdfs:
            merger.append(pdf)

        merger.write("output/letters/{}/{}/{}_to_{}/SEMvsSCADA.pdf".format(year_folder, month_folder, start_dt, end_dt))
        merger.close()
        messagebox.showinfo('Sections generation', "Sections and plots generated")