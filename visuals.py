"""Midnight Glass UI components; no network, map or analytics side effects."""
import math
from PySide6.QtCore import Qt,QRectF,QPointF,QPropertyAnimation,Property,QEasingCurve
from PySide6.QtGui import QColor,QFont,QPainter,QPen,QBrush,QLinearGradient,QPainterPath
from PySide6.QtWidgets import QWidget,QFrame,QLabel,QVBoxLayout,QHBoxLayout,QToolTip

DARK_STYLE='''
QWidget {font-family:"Segoe UI","Tahoma";font-size:13px;color:#dbe3f8;}
QMainWindow,QWidget#Root,QWidget#Body,QScrollArea {background:#090f20;}
QFrame#Sidebar {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #141a35,stop:1 #0c1429);border-left:1px solid #242b48;}
QFrame#Sidebar QLabel {background:transparent;color:#aab7db;}
QLabel#Brand {font-size:21px;font-weight:800;color:#f4f3ff;}
QLabel#Title {font-size:26px;font-weight:750;color:#f0efff;}
QLabel#Muted {color:#8794b7;font-size:12px;}
QLabel#Section {font-size:17px;font-weight:700;color:#e9eaff;}
QFrame#Card {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #151a31,stop:1 #0f172b);border:1px solid #2a3150;border-radius:17px;}
QFrame#KPI {background:transparent;border:0;}
QLabel#Value {font-size:30px;font-weight:800;color:#f5f3ff;}
QPushButton {background:#161f37;border:1px solid #303c5f;border-radius:11px;padding:11px 17px;font-weight:600;color:#dae3fb;}
QPushButton:hover {background:#242c4b;border-color:#7467bf;}
QPushButton:pressed {background:#302955;}
QPushButton:disabled {background:#11192b;color:#566181;border-color:#26304b;}
QPushButton#Primary {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #9b5cf4,stop:1 #6527da);border-color:#a080f6;color:white;}
QPushButton#Primary:hover {background:#9452ef;border-color:#c2a4ff;}
QPushButton#Nav {background:transparent;border:1px solid transparent;text-align:right;color:#98a7cf;font-size:14px;padding:15px 17px;border-radius:11px;}
QPushButton#Nav:hover {background:#1b2340;color:white;}
QPushButton#Nav:checked {background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #38205f,stop:1 #252849);border-color:#7c50cf;color:#f0eaff;}
QPushButton#Excel {background:#102a30;border-color:#28606a;color:#b0f3df;}
QPushButton#Excel:hover {background:#173941;border-color:#4da897;}
QComboBox {background:#111b30;border:1px solid #2c3958;border-radius:9px;min-height:32px;padding:3px 12px;min-width:85px;color:#c0cdec;}
QComboBox::drop-down {border:0;width:25px;}
QComboBox QAbstractItemView {background:#18223b;color:#dce4fa;selection-background-color:#413467;selection-color:white;}
QLineEdit {background:#101a2c;border:1px solid #34405e;border-radius:9px;padding:10px;color:#e1e7fa;}
QCheckBox {color:#97a5c9;spacing:8px;}
QTableWidget {background:#10192c;alternate-background-color:#141e34;border:0;gridline-color:#232f4a;selection-background-color:#3a2f60;selection-color:#eee7ff;}
QHeaderView::section {background:#1b243d;border:0;border-bottom:1px solid #303b59;padding:13px;color:#abb8d9;font-weight:600;}
QTableWidget::item {padding:9px;border-bottom:1px solid #202c46;}
QScrollBar:vertical {background:transparent;width:8px;margin:2px;}
QScrollBar::handle:vertical {background:#3c4668;border-radius:3px;min-height:30px;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0;}
QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical {background:transparent;}
QProgressBar {border:0;background:#1c2841;border-radius:3px;height:5px;}
QProgressBar::chunk {background:#ac78ff;border-radius:3px;}
QToolTip {background:#251d40;color:#eee6ff;padding:10px;border:1px solid #7055a4;}
QDialog {background:#10182b;}
QLabel {background:transparent;}
'''

def number(v):return f'{v:,.0f}'
def short(v):return f'{v/1000000:.1f}م' if v>=1000000 else (f'{v/1000:.0f}ه' if v>=1000 else number(v))

class Metric(QFrame):
    def __init__(self,title,symbol,color,subtitle):
        super().__init__();self.setObjectName('KPI');self.setMinimumHeight(147)
        self.color=QColor('#ac6aff' if 'مجموع هزینه' in title else '#40b9ff' if 'تعداد' in title else '#3ed2cd' if 'میانگین' in title else '#ed6f91')
        l=QVBoxLayout(self);l.setContentsMargins(20,19,20,19);l.setSpacing(10)
        row=QHBoxLayout();title_label=QLabel(title);title_label.setStyleSheet('color:#c6cce7;font-size:12px;');row.addWidget(title_label);row.addStretch()
        icon=QLabel(symbol);icon.setFixedSize(38,38);icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f'background:{self.color.darker(350).name()};color:{self.color.name()};border:1px solid {self.color.darker(200).name()};border-radius:17px;font-size:20px;font-weight:bold;');row.addWidget(icon);l.addLayout(row)
        self.value=QLabel('۰');self.value.setObjectName('Value');self.value.setLayoutDirection(Qt.LayoutDirection.LeftToRight);self.value.setAlignment(Qt.AlignmentFlag.AlignRight);l.addWidget(self.value)
        sub=QLabel(subtitle);sub.setStyleSheet('color:#8e9abc;font-size:11px;');l.addWidget(sub)
    def set(self,value):self.value.setText(str(value))
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);r=QRectF(self.rect()).adjusted(.5,.5,-.5,-.5)
        g=QLinearGradient(r.topRight(),r.bottomLeft());g.setColorAt(0,self.color.darker(600));g.setColorAt(.65,QColor('#141a30'));g.setColorAt(1,QColor('#101728'))
        p.setBrush(g);p.setPen(QPen(self.color.darker(330),1));p.drawRoundedRect(r,17,17);p.end()

class Plot(QWidget):
    def __init__(self,line=False):
        super().__init__();self.line=line;self.items=[];self.hit=[];self.hover=-1;self._reveal=1.;self.setMinimumHeight(242);self.setMouseTracking(True)
        self.animation=QPropertyAnimation(self,b'reveal');self.animation.setDuration(650);self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    def get_reveal(self):return self._reveal
    def set_reveal(self,v):self._reveal=v;self.update()
    reveal=Property(float,get_reveal,set_reveal)
    def set_data(self,items):
        if items==self.items:return
        self.items=items;self.animation.stop();self.animation.setStartValue(0.);self.animation.setEndValue(1.);self.animation.start()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);self.hit=[];left=48;right=self.width()-15;top=24;bottom=self.height()-41
        if not self.items or not any(v for _,v in self.items):
            p.setPen(QColor('#8795bb'));p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,'برای نمایش نمودار، اکسل را بارگذاری کنید');p.end();return
        maximum=max(v for _,v in self.items)*1.2;p.setFont(QFont('Segoe UI',8))
        for n in range(5):
            y=bottom-(bottom-top)*n/4;p.setPen(QPen(QColor('#2b3353'),1,Qt.PenStyle.DashLine));p.drawLine(QPointF(left,y),QPointF(right,y));p.setPen(QColor('#8e9bc0'));p.drawText(QRectF(0,y-10,left-7,20),Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter,short(maximum*n/4))
        step=(right-left)/len(self.items);points=[]
        for i,(title,value) in enumerate(self.items):
            x=left+step*(i+.5);y=bottom-(bottom-top)*value/maximum*self._reveal;points.append(QPointF(x,y))
            caption=title if step>=44 else ['فرو','ارد','خرد','تیر','مرد','شهر','مهر','آبا','آذر','دی','بهم','اسف'][i]
            p.setPen(QColor('#99a6c9'));p.drawText(QRectF(x-step/2,bottom+14,step,21),Qt.AlignmentFlag.AlignCenter,caption);self.hit.append((QRectF(x-step/2,top,step,bottom-top),title,value))
        path=QPainterPath(points[0])
        for a,b in zip(points,points[1:]):
            mid=(a.x()+b.x())/2;path.cubicTo(QPointF(mid,a.y()),QPointF(mid,b.y()),b)
        area=QPainterPath(path);area.lineTo(QPointF(points[-1].x(),bottom));area.lineTo(QPointF(points[0].x(),bottom));area.closeSubpath()
        color=QColor('#44d2c0' if self.line else '#b68aff');g=QLinearGradient(0,top,0,bottom);g.setColorAt(0,QColor(color.red(),color.green(),color.blue(),95));g.setColorAt(1,QColor(color.red(),color.green(),color.blue(),4));p.setPen(Qt.PenStyle.NoPen);p.setBrush(g);p.drawPath(area)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for width,alpha in [(9,12),(5,25),(2.6,255)]:p.setPen(QPen(QColor(color.red(),color.green(),color.blue(),alpha),width));p.drawPath(path)
        for point,(_,value) in zip(points,self.items):
            if not value:continue
            p.setBrush(color);p.setPen(QPen(QColor('#eee2ff'),1));p.drawEllipse(point,3,3)
        if 0<=self.hover<len(points):
            point=points[self.hover];p.setPen(QPen(QColor('#726296'),1,Qt.PenStyle.DashLine));p.drawLine(QPointF(point.x(),top),QPointF(point.x(),bottom));p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(180,137,255,55));p.drawEllipse(point,10,10);p.setBrush(QColor('#f5edff'));p.drawEllipse(point,4.5,4.5)
        p.end()
    def mouseMoveEvent(self,e):
        for i,(rect,title,value) in enumerate(self.hit):
            if rect.contains(e.position()):
                self.hover=i;self.update();QToolTip.showText(e.globalPosition().toPoint(),f'{title}\n{number(value)}'+(' سفر' if self.line else ' تومان'),self);return
        self.hover=-1;self.update();QToolTip.hideText()
    def leaveEvent(self,e):self.hover=-1;self.update();QToolTip.hideText()

class Donut(QWidget):
    def __init__(self):super().__init__();self.values=[];self.setMinimumSize(155,155);self.setMaximumHeight(220)
    def set_data(self,values):self.values=values;self.update()
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);size=min(self.width(),self.height())-32;r=QRectF((self.width()-size)/2,(self.height()-size)/2,size,size);total=sum(v for _,v in self.values)
        p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor('#28334d'),20));p.drawEllipse(r);start=90*16
        for i,(_,value) in enumerate(self.values):
            if not value:continue
            span=-int(value/(total or 1)*360*16);pen=QPen(QColor(['#32d9a2','#ffae59'][i%2]),20);p.setPen(pen);p.drawArc(r,start,span);start+=span
        cx=self.width()/2;cy=self.height()/2;p.setPen(QColor('#f0eeff'));p.setFont(QFont('Segoe UI',23,QFont.Weight.Bold));p.drawText(QRectF(cx-55,cy-28,110,40),Qt.AlignmentFlag.AlignCenter,number(total));p.setPen(QColor('#98a8c9'));p.setFont(QFont('Segoe UI',10));p.drawText(QRectF(cx-55,cy+15,110,24),Qt.AlignmentFlag.AlignCenter,'سفر');p.end()

class DestinationMap(QWidget):
    """Decorative schematic. No fabricated coordinates, route distances or real geography."""
    def __init__(self):super().__init__();self.names=[];self.setMinimumHeight(190)
    def set_data(self,items):self.names=[(n,c) for n,(c,_) in items[:3]];self.update()
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);w=self.width();h=self.height()
        p.setClipRect(self.rect());p.setPen(QPen(QColor('#1d2c49'),1))
        # Abstract street-like texture, deliberately not a geographic basemap.
        for i in range(-8,45):
            x=i*24;path=QPainterPath(QPointF(x,-10));path.cubicTo(x+45,h*.3,x-25,h*.6,x+70,h+20);p.drawPath(path)
        for j in range(13):
            y=j*19;path=QPainterPath(QPointF(-10,y));path.cubicTo(w*.3,y-25,w*.65,y+35,w+10,y-12);p.drawPath(path)
        points=[QPointF(w*.2,h*.26),QPointF(w*.48,h*.7),QPointF(w*.8,h*.39)]
        if not self.names:
            p.setPen(QColor('#8394b7'));p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,'مقصدهای پرتکرار اینجا نمایش داده می‌شوند');p.end();return
        path=QPainterPath(points[0]);path.cubicTo(w*.37,0,w*.22,h*.8,points[1].x(),points[1].y());path.cubicTo(w*.63,h*.85,w*.67,h*.24,points[2].x(),points[2].y())
        p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(175,120,255,25),9));p.drawPath(path);p.setPen(QPen(QColor('#9771e0'),1.7,Qt.PenStyle.DashLine));p.drawPath(path)
        for point,(name,count) in zip(points,self.names):
            p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(175,120,255,45));p.drawEllipse(point,13,13);p.setBrush(QColor('#a875ff'));p.drawEllipse(point,7,7);p.setBrush(QColor('#f0e8ff'));p.drawEllipse(point,3.5,3.5)
            caption=name if len(name)<=25 else name[:23]+'…';p.setPen(QColor('#d4dbf3'));p.setFont(QFont('Segoe UI',9));p.drawText(QRectF(point.x()-85,point.y()+17,170,24),Qt.AlignmentFlag.AlignCenter,caption)
        p.end()
