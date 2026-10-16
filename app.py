"""Native Qt frontend. Business logic and supplied browser expressions are unchanged."""
import os,sys,queue,threading
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QRectF,QPointF,QUrl,QSize,QPropertyAnimation,QEasingCurve
from PySide6.QtGui import QColor,QFont,QPainter,QPen,QLinearGradient,QPainterPath,QDesktopServices,QPixmap,QIcon
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QFrame,QLabel,QPushButton,QVBoxLayout,QHBoxLayout,
    QScrollArea,QStackedWidget,QComboBox,QCheckBox,QTableWidget,QTableWidgetItem,QHeaderView,QAbstractItemView,
    QFileDialog,QMessageBox,QDialog,QLineEdit,QDialogButtonBox,QProgressBar,QToolTip,QGraphicsOpacityEffect)
from core import MONTHS,g2j,j2g,today,load_xlsx,save_xlsx,stats,norm
from extract import run

STYLE='''
QWidget {font-family:"Segoe UI","Tahoma";font-size:13px;color:#25334f;}
QMainWindow,QWidget#Root,QWidget#Body,QScrollArea {background:#f4f6fb;}
QFrame#Sidebar {background:#111d36;border:0;}
QFrame#Sidebar QLabel {color:#c7d3ed;background:transparent;}
QLabel#Brand {font-size:21px;font-weight:800;color:white;}
QLabel#Title {font-size:25px;font-weight:750;color:#172541;}
QLabel#Muted {color:#8999b2;font-size:12px;}
QLabel#Section {font-size:17px;font-weight:700;color:#1d2d4d;}
QFrame#Card,QFrame#KPI {background:white;border:1px solid #e7ecf6;border-radius:18px;}
QLabel#Value {font-size:30px;font-weight:800;color:#192c51;}
QPushButton {background:white;border:1px solid #dde5f2;border-radius:10px;padding:11px 17px;font-weight:600;color:#334467;}
QPushButton:hover {background:#edf2ff;border-color:#c4d4ff;}
QPushButton:disabled {background:#eef1f7;color:#b0bbce;border-color:#e6eaf3;}
QPushButton#Primary {background:#5269ee;border-color:#5269ee;color:white;}
QPushButton#Primary:hover {background:#4259dd;}
QPushButton#Nav {background:transparent;border:0;text-align:right;color:#93a5c8;font-size:14px;padding:15px 17px;border-radius:11px;}
QPushButton#Nav:hover {background:#1a2b4d;color:white;}
QPushButton#Nav:checked {background:#273960;color:white;}
QComboBox {background:white;border:1px solid #e0e7f2;border-radius:9px;min-height:34px;padding:3px 12px;min-width:85px;color:#324461;}
QComboBox::drop-down {border:0;width:25px;}
QComboBox QAbstractItemView {background:white;color:#25334f;selection-background-color:#edf1ff;selection-color:#5269ee;}
QLineEdit {background:white;border:1px solid #dde5f2;border-radius:9px;padding:10px;}
QCheckBox {color:#73839e;spacing:8px;}
QTableWidget {background:white;alternate-background-color:#f9fbff;border:0;gridline-color:#eef2f8;selection-background-color:#edf1ff;selection-color:#263a67;}
QHeaderView::section {background:#f6f8fc;border:0;border-bottom:1px solid #e8edf5;padding:13px;color:#8090ab;font-weight:600;}
QTableWidget::item {padding:9px;border-bottom:1px solid #f0f3f9;}
QScrollBar:vertical {background:transparent;width:8px;margin:2px;}
QScrollBar::handle:vertical {background:#cbd5e5;border-radius:3px;min-height:30px;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0;}
QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical {background:transparent;}
QProgressBar {border:0;background:#e7ecfa;border-radius:3px;height:5px;}
QProgressBar::chunk {background:#677bf3;border-radius:3px;}
QToolTip {background:#172541;color:white;padding:10px;border:0;}
QDialog {background:#f4f6fb;}
QPushButton#Excel {background:#f0faf5;border-color:#cbe9d8;color:#167b48;}
QPushButton#Excel:hover {background:#e1f4e9;border-color:#91cfaf;}
'''
def number(v):return f'{v:,.0f}'
def short(v):return f'{v/1000000:.1f}م' if v>=1000000 else (f'{v/1000:.0f}ه' if v>=1000 else number(v))
def label(text,name=None):
    w=QLabel(text)
    if name:w.setObjectName(name)
    return w
def button(text,callback,primary=False):
    w=QPushButton(text);w.clicked.connect(callback);w.setCursor(Qt.CursorShape.PointingHandCursor)
    if primary:w.setObjectName('Primary')
    return w
def card():
    w=QFrame();w.setObjectName('Card');l=QVBoxLayout(w);l.setContentsMargins(22,20,22,20);l.setSpacing(14);return w,l

def excel_icon(upload=False):
    # Local vector-style spreadsheet + upload/download arrow; no external assets.
    pix=QPixmap(34,30);pix.fill(Qt.GlobalColor.transparent);p=QPainter(pix);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#e1f3e8'));p.drawRoundedRect(QRectF(5,2,19,25),3,3)
    p.setPen(QPen(QColor('#45a56f'),1))
    for y in [8,13,18,23]:p.drawLine(7,y,21,y)
    p.drawLine(14,6,14,24)
    p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#19864f'));p.drawRoundedRect(QRectF(0,8,13,14),2,2)
    p.setPen(QColor('white'));p.setFont(QFont('Segoe UI',9,QFont.Weight.Bold));p.drawText(QRectF(0,8,13,14),Qt.AlignmentFlag.AlignCenter,'X')
    p.setPen(QPen(QColor('#19864f'),2,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap));p.drawLine(28,7,28,22)
    tip=7 if upload else 22;tail=tip+5 if upload else tip-5
    p.drawLine(28,tip,24,tail);p.drawLine(28,tip,32,tail);p.end();return QIcon(pix)

def excel_button(text,callback,upload=False):
    w=button('',callback);w.setObjectName('Excel');w.setAccessibleName(text)
    layout=QHBoxLayout(w);layout.setContentsMargins(13,7,13,7);layout.setSpacing(11)
    icon=QLabel();icon.setPixmap(excel_icon(upload).pixmap(34,30));icon.setFixedSize(34,30)
    title=label(text);title.setStyleSheet('color:#b0f3df;font-weight:600;background:transparent;')
    for child in (icon,title):child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    layout.addWidget(icon);layout.addWidget(title);w.setMinimumHeight(48)
    w.setMinimumWidth(title.sizeHint().width()+100)
    return w

class Hero(QWidget):
    def __init__(self):super().__init__();self.setMinimumHeight(132)
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);r=QRectF(self.rect()).adjusted(0,0,-1,-1)
        g=QLinearGradient(r.topRight(),r.bottomLeft());g.setColorAt(0,QColor('#5966ed'));g.setColorAt(1,QColor('#8660e0'));p.setPen(Qt.PenStyle.NoPen);p.setBrush(g);p.drawRoundedRect(r,20,20)
        for x,y,radius in [(80,130,94),(130,30,50),(255,140,70)]:p.setBrush(QColor(255,255,255,15));p.drawEllipse(QPointF(x,y),radius,radius)
        path=QPainterPath(QPointF(28,92));path.cubicTo(90,10,130,120,185,51);path.cubicTo(228,0,260,106,318,35);p.setPen(QPen(QColor(255,255,255,100),2,Qt.PenStyle.DashLine));p.setBrush(Qt.BrushStyle.NoBrush);p.drawPath(path)
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#f7d98a'));p.drawEllipse(QPointF(185,51),6,6);p.setBrush(QColor('#adf3dd'));p.drawEllipse(QPointF(318,35),5,5)
        p.setPen(QColor('white'));p.setFont(QFont('Segoe UI',19,QFont.Weight.Bold));p.drawText(QRectF(320,25,self.width()-350,40),Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter,'هزینه‌های سفر، روشن و قابل‌فهم.')
        p.setPen(QColor('#e4e6ff'));p.setFont(QFont('Segoe UI',10));p.drawText(QRectF(320,73,self.width()-350,30),Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter,'از تاریخچه اسنپ و تپسی، به تصویر دقیق‌تری از رفت‌وآمدها برسید.');p.end()

from visuals import Metric,Plot,Donut,DestinationMap,DARK_STYLE
STYLE=DARK_STYLE

class App(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('Ride Insight • تحلیل سفر');self.resize(1360,880);self.setMinimumSize(1060,620)
        self.rides={};self.events=queue.Queue();self.ready=threading.Event();self.stop_event=threading.Event();self.worker=None;self.last_output=None;self.anchor=today()
        self.output_dir=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'RideInsight'/'exports';self.output_dir.mkdir(parents=True,exist_ok=True);self.build();self.timer=QTimer(self);self.timer.timeout.connect(self.poll);self.timer.start(150);self.refresh()
    def build(self):
        root=QWidget();root.setObjectName('Root');root.setLayoutDirection(Qt.LayoutDirection.LeftToRight);self.setCentralWidget(root);row=QHBoxLayout(root);row.setContentsMargins(0,0,0,0);row.setSpacing(0);row.setDirection(QHBoxLayout.Direction.LeftToRight)
        content=QWidget();content.setLayoutDirection(Qt.LayoutDirection.RightToLeft);outer=QVBoxLayout(content);outer.setContentsMargins(30,25,30,20);outer.setSpacing(16);row.addWidget(content,1)
        sidebar=QFrame();sidebar.setObjectName('Sidebar');sidebar.setLayoutDirection(Qt.LayoutDirection.RightToLeft);sidebar.setFixedWidth(205);self.sidebar=sidebar;side=QVBoxLayout(sidebar);side.setContentsMargins(18,30,18,22);side.setSpacing(8);row.addWidget(sidebar)
        brand=label('RIDE INSIGHT','Brand');brand.setAlignment(Qt.AlignmentFlag.AlignCenter);brand.setLayoutDirection(Qt.LayoutDirection.LeftToRight);side.addWidget(brand);sub=label('تصویر روشن رفت‌وآمدها');sub.setAlignment(Qt.AlignmentFlag.AlignCenter);sub.setStyleSheet('color:#7286ad;font-size:11px;');side.addWidget(sub);side.addSpacing(33)
        self.nav=[]
        for i,(icon,name) in enumerate([('▦','نمای کلی'),('≋','گزارش ماهانه'),('◎','مقصدهای پرتکرار'),('▤','جزئیات سفر'),('◇','راهنما و کیفیت')]):
            b=QPushButton(f'{icon}    {name}');b.setObjectName('Nav');b.setCheckable(True);b.setCursor(Qt.CursorShape.PointingHandCursor);b.clicked.connect(lambda checked,n=i:self.navigate(n));side.addWidget(b);self.nav.append(b)
        side.addStretch();badge=label('●   داده‌ها روی دستگاه شما');badge.setStyleSheet('color:#7dccb9;font-size:11px;');side.addWidget(badge);folder=button('پوشه خروجی  ↗',self.open_folder);folder.setStyleSheet('background:#1b2340;color:#b5c2e3;border:1px solid #303958;');side.addWidget(folder);side.addWidget(label('MIDNIGHT EDITION / 1.3','Muted'))
        header=QHBoxLayout();titles=QVBoxLayout();self.page_title=label('نمای کلی سفرها','Title');titles.addWidget(self.page_title);titles.addWidget(label('کنترل هزینه‌ها، به تفکیک سرویس، سال و ماه','Muted'));header.addLayout(titles);header.addStretch()
        self.import_btn=excel_button('بارگذاری فایل اکسل',self.import_file,True);self.import_btn.setToolTip('فایل سفرهای اسنپ یا تپسی را برای تحلیل انتخاب کنید.');header.addWidget(self.import_btn)
        self.export_btn=excel_button('ذخیره گزارش در اکسل',self.export_file);self.export_btn.setToolTip('محل ذخیره فایل اکسل را انتخاب کنید.');header.addWidget(self.export_btn)
        self.start_btn=button('+  استخراج سفرها',self.start,True);header.addWidget(self.start_btn);outer.addLayout(header)
        filters=QHBoxLayout();self.provider=QComboBox();self.provider.addItems(['همه سرویس‌ها','اسنپ','تپسی']);self.year_box=QComboBox();self.year_box.addItem('همه سال‌ها');self.month_box=QComboBox();self.month_box.addItems(['همه ماه‌ها']+MONTHS)
        filters.addWidget(label('سرویس','Muted'));filters.addWidget(self.provider);self.provider.currentIndexChanged.connect(self.refresh)
        self.year_box.currentIndexChanged.connect(self.refresh);self.month_box.currentIndexChanged.connect(self.refresh)
        filters.addStretch();self.date_btn=button('◷  '+ '/'.join(map(str,g2j(today()))),self.edit_anchor);filters.addWidget(self.date_btn);outer.addLayout(filters)
        self.progress_frame=QFrame();self.progress_frame.setObjectName('Card');pl=QVBoxLayout(self.progress_frame);pr=QHBoxLayout();self.progress_label=label('');self.progress_label.setWordWrap(True);pr.addWidget(self.progress_label,1);self.ready_btn=button('ورود انجام شد',self.confirm_ready,True);pr.addWidget(self.ready_btn);self.stop_btn=button('توقف و ذخیره',self.stop);pr.addWidget(self.stop_btn);pl.addLayout(pr);self.progress=QProgressBar();self.progress.setRange(0,0);self.progress.setTextVisible(False);pl.addWidget(self.progress);outer.addWidget(self.progress_frame);self.progress_frame.hide()
        self.stack=QStackedWidget();outer.addWidget(self.stack,1)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.Shape.NoFrame);body=QWidget();body.setObjectName('Body');dash=QVBoxLayout(body);dash.setContentsMargins(0,0,7,0);dash.setSpacing(17);scroll.setWidget(body);self.stack.addWidget(scroll);metrics=QHBoxLayout();metrics.setSpacing(13);self.metrics={}
        for key,title,icon,color,subtitle in [('total','مجموع هزینه • تومان','↗','#6274ec','فقط سفرهای بدون علامت لغو'),('count','تعداد سفرها','▦','#27bda5','در محدوده انتخاب‌شده'),('average','میانگین کرایه • تومان','≈','#9b6bd7','مجموع هزینه تقسیم بر تعداد'),('cancel','سفرهای لغوشده','×','#e59a69','حذف‌شده از محاسبات')]:
            box=Metric(title,icon,color,subtitle);metrics.addWidget(box,1);self.metrics[key]=box
        dash.addLayout(metrics);charts=QHBoxLayout();charts.setSpacing(16)
        cost,cl=card();heading=QHBoxLayout();self.cost_title=label('روند هزینه سفرها','Section');heading.addWidget(self.cost_title);heading.addStretch()
        self.chart_mode=QComboBox();self.chart_mode.addItems(['هزینه سفر','تعداد سفر']);heading.addWidget(self.chart_mode);cl.addLayout(heading)
        cl.addWidget(label('مقادیر دقیق با حرکت نشانگر روی نمودار نمایش داده می‌شوند.','Muted'))
        self.plot_stack=QStackedWidget();self.cost_plot=Plot();self.count_plot=Plot(True);self.plot_stack.addWidget(self.cost_plot);self.plot_stack.addWidget(self.count_plot);self.chart_mode.currentIndexChanged.connect(self.plot_stack.setCurrentIndex);cl.addWidget(self.plot_stack)
        self.count_title=QLabel();charts.addWidget(cost,3)
        share,sl=card();sl.addWidget(label('سهم سرویس‌ها','Section'));sr=QHBoxLayout();self.donut=Donut();sr.addWidget(self.donut,1);leg=QVBoxLayout();self.share_labels=[]
        for name,color in [('اسنپ','#32d9a2'),('تپسی','#ffae59')]:
            entry=label('●  '+name);entry.setStyleSheet(f'color:{color};font-weight:700;font-size:14px;');leg.addWidget(entry);value=label('۰ سفر','Muted');leg.addWidget(value);self.share_labels.append(value)
        sr.addLayout(leg);sl.addLayout(sr);sl.addWidget(label('سهم از تعداد سفرهای بدون علامت لغو','Muted'));charts.addWidget(share,2);dash.addLayout(charts)
        bottom=QHBoxLayout();bottom.setSpacing(16)
        route,route_layout=card();route_layout.addWidget(label('مقصدهای شما، در یک نگاه','Section'))
        self.destination_map=DestinationMap();route_layout.addWidget(self.destination_map)
        route_layout.addWidget(label('نمای شماتیک • موقعیت نقاط و اتصال‌ها جغرافیایی نیستند.','Muted'));bottom.addWidget(route,3)
        top,tl=card();tl.addWidget(label('مقصدهای محبوب','Section'));tl.addWidget(label('رتبه‌بندی بر اساس تعداد سفر','Muted'));self.top_labels=[]
        for i in range(3):
            item=QHBoxLayout();rank=label(f'0{i+1}');rank.setStyleSheet('color:#aa8dde;font-weight:bold;');item.addWidget(rank)
            name=label('—');name.setWordWrap(True);item.addWidget(name,1);num=label('');num.setStyleSheet('color:#c29bff;font-weight:700;');item.addWidget(num);tl.addLayout(item);self.top_labels.append((name,num))
        bottom.addWidget(top,2);dash.addLayout(bottom);dash.addStretch()
        report=QWidget();rl=QVBoxLayout(report);rl.setContentsMargins(0,0,0,0);rl.setSpacing(12);self.stack.addWidget(report)
        self.compare_toggle=QCheckBox('نمایش مقایسه سالانه و سرویس‌ها');rl.addWidget(self.compare_toggle)
        rf,rfl=card();rfl.addWidget(label('مقایسه سالانه و سرویس‌ها','Section'));self.service_table=self.table(['سرویس / سال','تعداد سفر','مجموع تومان','میانگین تومان']);self.service_table.setMaximumHeight(150);rfl.addWidget(self.service_table);rl.addWidget(rf);rf.hide();self.compare_toggle.toggled.connect(rf.setVisible)
        mf,ml=card();ml.addWidget(label('جزئیات هزینه ماهانه','Section'));monthly_filters=QHBoxLayout()
        for title,box in [('سال',self.year_box),('ماه',self.month_box)]:monthly_filters.addWidget(label(title,'Muted'));monthly_filters.addWidget(box)
        monthly_filters.addStretch();monthly_filters.addWidget(button('پاک‌کردن فیلترها',self.reset_report_filters));ml.addLayout(monthly_filters)
        self.month_summary=label('','Muted');ml.addWidget(self.month_summary);self.month_table=self.table(['سال','ماه','تعداد سفر','مجموع تومان','میانگین تومان']);self.month_table.setMinimumHeight(210);ml.addWidget(self.month_table,1);rl.addWidget(mf,1)
        dest,dl=card();dl.addWidget(label('مقصدهای پرتکرار','Section'));dl.addWidget(label('گروه‌بندی در سطح محدوده است، نه یک پلاک مشخص.','Muted'));self.dest_table=self.table(['محدوده مقصد','تعداد سفر','مجموع تومان','سهم تعداد']);dl.addWidget(self.dest_table);self.stack.addWidget(dest)
        details,d_l=card();dhead=QHBoxLayout();dhead.addWidget(label('جزئیات و اصلاح تاریخ','Section'));dhead.addStretch();dhead.addWidget(button('اصلاح تاریخ انتخاب‌شده',self.edit_date));d_l.addLayout(dhead);self.strict=QCheckBox('فقط تاریخ‌های صریح یا اصلاح‌شده');self.strict.stateChanged.connect(self.refresh);d_l.addWidget(self.strict);self.detail_table=self.table(['سرویس','تاریخ شمسی','وضعیت','تومان','مقصد','بررسی تاریخ']);d_l.addWidget(self.detail_table);self.stack.addWidget(details)
        quality,ql=card();ql.addWidget(label('داده شفاف، گزارش قابل بررسی','Section'));self.quality=QLabel();self.quality.setWordWrap(True);self.quality.setAlignment(Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignRight);self.quality.setStyleSheet('color:#a1b0d2;font-size:14px;');qs=QScrollArea();qs.setWidgetResizable(True);qs.setFrameShape(QFrame.Shape.NoFrame);qs.setWidget(self.quality);ql.addWidget(qs);self.stack.addWidget(quality)
        foot=QHBoxLayout();self.status_label=label('برای شروع، استخراج کنید یا یک اکسل وارد کنید.','Muted');self.status_label.setWordWrap(True);foot.addWidget(self.status_label,1);self.range_label=label('','Muted');foot.addWidget(self.range_label);outer.addLayout(foot);self.navigate(0)
    def table(self,headers):
        t=QTableWidget(0,len(headers));t.setHorizontalHeaderLabels(headers);t.setAlternatingRowColors(True);t.setShowGrid(False);t.verticalHeader().hide();t.verticalHeader().setDefaultSectionSize(44);t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection);t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);return t
    def fill(self,table,rows,keys=None):
        table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for j,value in enumerate(row):
                item=QTableWidgetItem(str(value));item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                if keys:item.setData(Qt.ItemDataRole.UserRole,keys[i])
                table.setItem(i,j,item)
    def navigate(self,index):
        self.stack.setCurrentIndex(index)
        if not hasattr(self,'page_effect'):
            self.page_effect=QGraphicsOpacityEffect(self.stack);self.stack.setGraphicsEffect(self.page_effect)
            self.page_animation=QPropertyAnimation(self.page_effect,b'opacity',self);self.page_animation.setDuration(180);self.page_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.page_animation.stop();self.page_animation.setStartValue(.65);self.page_animation.setEndValue(1.);self.page_animation.start()
        self.page_title.setText(['نمای کلی سفرها','گزارش ماهانه','مقصدهای پرتکرار','جزئیات سفر','راهنما و کیفیت'][index])
        for i,b in enumerate(self.nav):b.setChecked(i==index)
    def selected(self):
        p=self.provider.currentText();strict=self.strict.isChecked() if hasattr(self,'strict') else False
        return [r for r in self.rides.values() if (p.startswith('همه') or r.provider==p) and (not strict or bool(r.year) and 'استنباطی' not in r.note and 'نسبی' not in r.note)]

    def reset_report_filters(self):
        self.year_box.blockSignals(True);self.month_box.blockSignals(True);self.year_box.setCurrentIndex(0);self.month_box.setCurrentIndex(0);self.year_box.blockSignals(False);self.month_box.blockSignals(False);self.refresh()

    def export_selection(self):
        rows=self.selected()
        if self.stack.currentIndex()!=1:return rows
        year=self.year_box.currentText();month=self.month_box.currentText()
        return [r for r in rows if (year.startswith('همه') or str(r.year)==year)
                and (month.startswith('همه') or r.month==MONTHS.index(month)+1)]
    def refresh(self,*args):
        if not hasattr(self,'strict'):return
        year=self.year_box.currentText();years=sorted({r.year for r in self.rides.values() if r.year},reverse=True);choices=['همه سال‌ها']+list(map(str,years));self.year_box.blockSignals(True);self.year_box.clear();self.year_box.addItems(choices);self.year_box.setCurrentText(year if year in choices else choices[0]);self.year_box.blockSignals(False)
        selected=self.selected();s=stats(selected)
        for k,v in [('total',number(s['total'])),('count',number(s['count'])),('average',number(s['total']/s['count'] if s['count'] else 0)),('cancel',number(s['cancelled']))]:self.metrics[k].set(v)
        cy=max(s['years'],default=g2j(today())[0]);self.cost_title.setText(f'روند هزینه سفرها • {cy}');self.count_title.setText(f'روند تعداد سفر {cy}');self.cost_plot.set_data([(MONTHS[m-1],s['months'].get((cy,m),[0,0])[1]) for m in range(1,13)]);self.count_plot.set_data([(MONTHS[m-1],s['months'].get((cy,m),[0,0])[0]) for m in range(1,13)])
        annual=[(str(y),c,number(cost),number(cost/c)) for y,(c,cost) in sorted(s['years'].items(),reverse=True)];shares=[]
        for i,p in enumerate(['اسنپ','تپسی']):
            values=[r.amount for r in s['valid'] if r.provider==p];shares.append((p,len(values)));self.share_labels[i].setText(f'{len(values):,} سفر • {len(values)/(s["count"] or 1)*100:.0f}٪')
            if values:annual.append((p,len(values),number(sum(values)),number(sum(values)/len(values))))
        self.donut.set_data(shares);self.fill(self.service_table,annual)
        report_months=[((y,m),(c,cost)) for (y,m),(c,cost) in sorted(s['months'].items(),reverse=True)
                       if (self.year_box.currentText().startswith('همه') or str(y)==self.year_box.currentText())
                       and (self.month_box.currentText().startswith('همه') or MONTHS[m-1]==self.month_box.currentText())]
        self.fill(self.month_table,[(y,MONTHS[m-1],c,number(cost),number(cost/c)) for (y,m),(c,cost) in report_months])
        self.month_summary.setText(f'{len(report_months)} ماه  •  {sum(c for _,(c,_) in report_months):,} سفر  •  مجموع {number(sum(cost for _,(_,cost) in report_months))} تومان')
        destinations=sorted(s['dest'].items(),key=lambda x:-x[1][0]);self.destination_map.set_data(destinations);self.fill(self.dest_table,[(d,c,number(cost),f'{c/(s["count"] or 1)*100:.1f}٪') for d,(c,cost) in destinations])
        for i,(name,value) in enumerate(self.top_labels):
            if i<len(destinations):d,(c,cost)=destinations[i];name.setText(d);value.setText(f'{c} سفر')
            else:name.setText('—');value.setText('')
        self.fill(self.detail_table,[(r.provider,r.jalali,r.status,number(r.amount) if r.amount is not None else '',r.destination,r.note) for r in selected],[r.key for r in selected]);dates=[r.jalali for r in s['valid'] if r.jalali];self.range_label.setText((min(dates)+' تا '+max(dates)) if dates else '')
        info=[f'رکوردهای انتخاب‌شده: {len(selected):,}   |   لغوهای حذف‌شده: {s["cancelled"]:,}',f'بدون مبلغ و بدون علامت لغو: {s["missing"]:,} — وارد هزینه نشده است.',f'بدون تاریخ ولی دارای مبلغ: {s["undated"]:,} — در مجموع کل هست؛ در جدول سال/ماه نیست.']
        if s['valid']:
            low=min(s['valid'],key=lambda r:r.amount);high=max(s['valid'],key=lambda r:r.amount);info.extend([f'ارزان‌ترین سفر: {number(low.amount)} تومان — {low.jalali}',f'گران‌ترین سفر: {number(high.amount)} تومان — {high.jalali}'])
        info.extend(['وضعیت خالی یعنی علامت لغو دیده نشده؛ تأیید مستقل پرداخت نیست. لغوها همیشه از جمع هزینه و تعداد حذف می‌شوند.','سال بدون سال صریح از ترتیب سفرها و روز هفته استنباط می‌شود. فاصله‌های چندساله می‌تواند مبهم باشد؛ تاریخ را در جزئیات اصلاح کنید.','نمودارها در حالت همه سال‌ها جدیدترین سال را نشان می‌دهند. صفر یعنی رکوردی در داده انتخابی نیست.','تاریخ نسبی از زمان استخراج فایل تعیین می‌شود. برای فایل فاقد زمان استخراج از دکمه تاریخ بالا تاریخ مبنا را وارد کنید.','قبل از ورود اکسل قدیمی سرویس درست را انتخاب کنید. فایل جدید ستون سرویس دارد.','کلید متن/سرویس برای ادغام فایل‌های هم‌پوشان استفاده می‌شود؛ سفرهای با متن کاملاً یکسان ممکن است ادغام شوند.','اکسل قدیمی تپسی ممکن است لغوهای بدون مبلغ را نداشته باشد؛ برای گزارش معتبر دوباره استخراج کنید.','ریال به تومان تبدیل می‌شود. تخفیف و بازپرداخت مستقل از کرایه قابل تشخیص نیست.','۲۰ ثانیه توقف در انتهای صفحه تضمین نمی‌کند تمام سفرها بارگذاری شده باشند.','داده فقط روی دستگاه ذخیره می‌شود. فایل خروجی می‌تواند آدرس‌های شخصی داشته باشد.']);self.quality.setText('\n\n'.join(info))
    def choose_provider(self,title):
        d=QDialog(self);d.setWindowTitle(title);d.setMinimumWidth(370);l=QVBoxLayout(d);l.setContentsMargins(25,25,25,25);l.setSpacing(16);l.addWidget(label(title,'Section'));box=QComboBox();box.addItems(['اسنپ','تپسی']);box.setCurrentText(self.provider.currentText() if self.provider.currentText() in ['اسنپ','تپسی'] else 'اسنپ');l.addWidget(box);b=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);b.button(QDialogButtonBox.StandardButton.Ok).setText('ادامه');b.button(QDialogButtonBox.StandardButton.Cancel).setText('انصراف');b.accepted.connect(d.accept);b.rejected.connect(d.reject);l.addWidget(b);return box.currentText() if d.exec()==QDialog.DialogCode.Accepted else None
    def start(self):
        if self.worker and self.worker.is_alive():return
        provider=self.choose_provider('استخراج تاریخچه سفرها')
        if not provider:return
        self.ready.clear();self.stop_event.clear();self.anchor=today();self.last_output=self.output_dir/(('Snapp' if provider=='اسنپ' else 'Tapsi')+'_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.xlsx');self.start_btn.setEnabled(False);self.progress_frame.show();self.ready_btn.setEnabled(False);self.stop_btn.setEnabled(True);self.progress_label.setText('مرورگر در حال باز شدن است…');self.worker=threading.Thread(target=run,args=(provider,self.last_output,self.anchor,self.events,self.ready,self.stop_event),daemon=True);self.worker.start()
    def confirm_ready(self):self.ready.set();self.ready_btn.setEnabled(False);self.progress_label.setText('استخراج شروع شد؛ مرورگر را نبندید.')
    def stop(self):self.stop_event.set();self.ready.set();self.progress_label.setText('در حال توقف و ذخیره اطلاعات…')
    def poll(self):
        try:
            while True:
                kind,data=self.events.get_nowait()
                if kind=='login':self.progress_label.setText(data);self.ready_btn.setEnabled(True)
                elif kind=='progress':self.progress_label.setText(data)
                elif kind=='data':
                    rides,path,reason=data;self.rides.update({r.key:r for r in rides});self.last_output=Path(path);self.status_label.setText(f'{len(rides):,} رکورد ذخیره شد • فایل در پوشه خروجی');self.status_label.setToolTip(path+'\n'+reason);self.refresh();self.navigate(0)
                elif kind=='error':QMessageBox.warning(self,'خطا',data);self.status_label.setText('استخراج با خطا متوقف شد؛ خروجی ذخیره‌شده را بررسی کنید.')
                elif kind=='finished':self.start_btn.setEnabled(True);self.progress_frame.hide();self.ready_btn.setEnabled(False);self.stop_btn.setEnabled(False)
        except queue.Empty:pass
    def ask_date(self,title,initial):
        d=QDialog(self);d.setWindowTitle(title);d.setMinimumWidth(410);l=QVBoxLayout(d);l.setContentsMargins(24,24,24,24);l.addWidget(label(title,'Section'));entry=QLineEdit(initial);entry.setLayoutDirection(Qt.LayoutDirection.LeftToRight);entry.setAlignment(Qt.AlignmentFlag.AlignCenter);l.addWidget(entry);l.addWidget(label('قالب تاریخ: 1405/07/22','Muted'));box=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);box.button(QDialogButtonBox.StandardButton.Ok).setText('ذخیره');box.button(QDialogButtonBox.StandardButton.Cancel).setText('انصراف');box.accepted.connect(d.accept);box.rejected.connect(d.reject);l.addWidget(box)
        if d.exec()!=QDialog.DialogCode.Accepted:return None
        try:parts=tuple(map(int,norm(entry.text()).split('/')));j2g(*parts);return parts
        except Exception:QMessageBox.warning(self,'تاریخ','تاریخ معتبر با قالب سال/ماه/روز وارد کنید.');return None
    def edit_anchor(self):
        parts=self.ask_date('تاریخ مبنا برای فایل فاقد زمان استخراج','/'.join(map(str,g2j(self.anchor))))
        if parts:self.anchor=j2g(*parts);self.date_btn.setText('◷  '+ '/'.join(map(str,parts)))
    def import_file(self):
        path,_=QFileDialog.getOpenFileName(self,'ورود اکسل','','Excel (*.xlsx)')
        if not path:return
        provider=self.choose_provider('سرویس فایل اکسل قدیمی')
        if not provider:return
        try:
            try:rides,anchor=load_xlsx(path,provider)
            except ValueError as e:
                if 'زمان استخراج' not in str(e):raise
                rides,anchor=load_xlsx(path,provider,self.anchor)
            self.rides.update({r.key:r for r in rides});self.status_label.setText(f'{len(rides):,} رکورد وارد شد • فایل‌های هم‌پوشان ادغام شدند');self.status_label.setToolTip(path);self.refresh();self.navigate(0)
        except Exception as e:QMessageBox.warning(self,'ورود فایل',str(e))
    def export_file(self):
        if not self.rides:QMessageBox.information(self,'خروجی','ابتدا استخراج کنید یا اکسل وارد کنید.');return
        path,_=QFileDialog.getSaveFileName(self,'خروجی اکسل','Ride_Insight_Report.xlsx','Excel (*.xlsx)')
        if not path:return
        if not path.lower().endswith('.xlsx'):path+='.xlsx'
        try:save_xlsx(path,self.export_selection(),self.anchor,'خروجی داشبورد؛ فیلتر فعلی');self.status_label.setText('خروجی اکسل ذخیره شد');self.status_label.setToolTip(path)
        except Exception as e:QMessageBox.warning(self,'ذخیره',str(e))
    def edit_date(self):
        row=self.detail_table.currentRow()
        if row<0:return
        ride=self.rides[self.detail_table.item(row,0).data(Qt.ItemDataRole.UserRole)];parts=self.ask_date('اصلاح تاریخ سفر',ride.jalali or '/'.join(map(str,g2j(today()))))
        if parts:y,m,d=parts;ride.year=y;ride.month=m;ride.jalali=f'{y:04}/{m:02}/{d:02}';ride.note='تاریخ اصلاح‌شده دستی';self.refresh()
    def open_folder(self):QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.output_dir)))
    def closeEvent(self,e):
        if self.worker and self.worker.is_alive():self.stop();self.status_label.setText('برای ذخیره خروجی صبر کنید؛ سپس پنجره را ببندید.');e.ignore()
        else:e.accept()

def application():
    app=QApplication.instance() or QApplication(sys.argv);app.setLayoutDirection(Qt.LayoutDirection.RightToLeft);app.setFont(QFont('Segoe UI',10));app.setStyleSheet(STYLE);return app
if __name__=='__main__':
    qt=application();window=App();window.showMaximized();sys.exit(qt.exec())
