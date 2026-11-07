import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from pathlib import Path
import io
#import zipfile

# Параметры вагона-эталона
Lce, le, baza_tel_e = 13.92, 8.65, 1.85
ne_zv, ne, nea = (Lce-le)/2-0.61, (Lce-le)/2,  (Lce-le)/2-0.87 

# Функция горка
def h(x:float)->float:
    xt1=50-250*0.055/np.sqrt(0.055**2+4)
    xt2=50+250*0.055/np.sqrt(0.055**2+4)
    condlist=[x<=xt1,(x>xt1) & (x<xt2), x>=xt2]
    funclist=[lambda x:x*0.055/2,lambda x:0.055/2*xt1-500/np.sqrt(0.055**2+4)+np.sqrt(250**2-(x-50)**2),lambda x:5.5/np.sqrt(0.055**2+4)-0.055/2*x]
    return np.piecewise(x,condlist,funclist)

# Функция аппарель
def ha(x,r,uklon:float)->float:
    xt1=50
    xt2=50+r*np.sin(uklon/1000)
    yt2=r-r*np.cos(uklon/1000)
    condlist=[x<=xt1,(x>xt1) & (x<xt2), x>=xt2]
    funclist=[lambda x:0, lambda x:r-np.sqrt(r*r-(x-xt1)**2),lambda x:yt2+(x-xt2)*uklon/1000]
    return np.piecewise(x,condlist,funclist)

def toFixed(numObj, digits=0):
    ss=f"{numObj:.{digits}f}"
    ss=ss.replace('.', ',')
    return ss

st.markdown('<h1 style="font-size: 2.5rem; white-space: nowrap;">Расчет прохождения горок и кривых</h1>', unsafe_allow_html=True)
st.write("Привет! Данное приложение предназначено для расчета и оформления отчета по прохождению горок и кривых ")

# Используем текущую рабочую директорию как корень проекта
PROJECT_ROOT = Path.cwd()
gfiles_dir = PROJECT_ROOT / "gfiles"

tab1, tab2 = st.tabs(["__Исходные данные__", "__Результаты расчета__"])
with tab1:
    model  = st.text_input("__Модель вагона__", value="15-6744")
    ipadez = st.text_input("__Наименование вагона в именительном падеже__", value="Полувагон универсальный с разгрузочными люками")
    rpadez = st.text_input("__Наименование вагона в родительном падеже__",  value="Полувагона универсального с разгрузочными люками")
    number = st.text_input("__Обозначение расчета__", value="ЦДЛР.1522.00.00.000")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        l        = st.number_input("__База вагона__",             value=8.65)
        Lc       = st.number_input("__Длина по осям сцепления__", value=13.92)
        baza_tel = st.number_input("__База тележки__",            value=1.85)
        avtoscep = st.selectbox("__Тип автосцепки__", list(enumerate(["CA-3", "CA-3M", "CA-3T"])), format_func=lambda x: x[1], index=0)[0]
        upor     = st.selectbox("__Тип переднего упора__", list(enumerate(["УП1", "УП3"])),format_func=lambda x: x[1], index=0)[0]
        typ_vag  = st.selectbox("__Тип вагона__", list(enumerate(["4-осный", "6-осный сочлененный","6-осный на 3-осных тележках", "8-осный на спаренных двухосных тележках"])),format_func=lambda x: x[1], index=0)[0]
    with col3:
        fio=[st.text_input(f"__ФИО {i+1}__", value=v) for i, v in enumerate(["Никитченко", "Куканов", "Конищев", "Туленцева", "Меркулов"])]

with tab2:
    [baza_tel, λ] = [np.sqrt(2*baza_tel), 0.013] if typ_vag == 2 else [baza_tel, 0.026]
    dh_dop=0.180 if avtoscep==0 else 0.250
    [gruppa,R_kr,R_s,R_a]=[1,80,120,135] if Lc<=21 else [2,110,160,250]
    n_zv=(Lc-l)/2-0.61
    n=(Lc-l)/2
    na=(Lc-l)/2-0.87
    
    Bs=0.175 if avtoscep==0 else 0.2
    beta0=(l/2+n)/R_a*180/np.pi
    B_left=Bs*(1.655*np.sin(65*np.pi/180-beta0*np.pi/180)-0.5)
    B_right=(n*(l+n)-(baza_tel/2)**2)/(2*R_a)+λ
    
    value=f"    {B_left:.3f} > {B_right:.3f}"
    formula = r"Сцепляемость\: обеспечена\: B\ge \frac{n\left( 2l+n \right)-l_т^{2}}{2R}+\lambda; \:" + value 
    st.latex(formula)
    
    b    =[((le+nea)*nea-(baza_tel_e/2)**2-0.87**2)/(2*R_s),((l+na)*na-(baza_tel/2)**2-0.87**2)/(2*R_s),0]
    bs   =[b[1],b[1],((l+na)*na-(baza_tel/2)**2-0.87**2)/(2*R_kr)]
    dzeta=[0.002, 0.043, 0.032]
    gama =np.array([np.arcsin((b[i]+bs[i]+dzeta[i])/(2*0.87))*180/np.pi for i in range(3)])
    beta =[np.arctan((le/2+nea+0.87)/R_s)*180/np.pi,np.arctan((l/2+na+0.87)/R_s)*180/np.pi,0.0]
    betas=[beta[1],beta[1],np.arctan((l/2+na+0.87)/R_kr)*180/np.pi]
    alfa =np.array(beta) + gama
    alfas=np.array(betas) + gama
    
    X_UP1 =[0,4,10.3,12.3,12.3];             Y_UP1 =[12.5,12.5,10.2,4,0]
    X_UP3 =[0,17,17.3,18,18.3,18.5,19,19];   Y_UP3 =[19,19,18.85,18.5,18.3,18,17,0]
    X_UP13=[0,16,17.8,19.6,19.6];            Y_UP13=[12,12,11.2,4,0]
    
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.set_xlabel(r'$\alpha$'+u'\u0027'+', градусы', fontsize=20)
    ax.set_ylabel(r'$\alpha$'+', градусы', fontsize=20)
    ax.grid(visible=True, which='both', color='k', linestyle='-', linewidth=1)
    ax.tick_params(axis='both', which='major', width=1, labelsize=20)
    plt.rc('axes', linewidth=2)    
    plt.rc('lines', linewidth=4)
    if upor==0:
        ax.set_xlim([0, 15])
        ax.set_ylim([0, 13])
        ax.plot(X_UP1, Y_UP1, color='k')
    else:
        ax.set_xlim([0, 20])
        ax.set_ylim([0, 20])
        ax.plot(X_UP3, Y_UP3, color='k')
        ax.plot(X_UP13, Y_UP13, color='k',linestyle="--")
    ax.plot(alfas[0],alfa[0],'ko',markersize=14)
    ax.plot(alfas[1],alfa[1],'ks',markersize=14)
    ax.plot(alfas[2],alfa[2],'k^',markersize=14)
    if upor==0:
        ax.legend(['Сочетание упоров типа УП1 и УП1','1-проектируемый и эталонный на S-образной кривой R'+str(R_s),'2-сцеп двух проектируемых на S-образной кривой R'+str(R_s),'3-проектируемый и эталонный на участке сопряжения прямой и кривой R'+str(R_kr)],shadow=True, fontsize=20, loc="lower left", ncol=1,bbox_to_anchor=(-0.0, -0.4),fancybox=True,borderaxespad=0.)
    else:
        ax.legend(['Сочетание упоров типа УП3 и УП3','Сочетание упоров типов УП3 и УП1','1-проектируемый и эталонный на S-образной кривой R'+str(R_s),'2-сцеп двух проектируемых на S-образной кривой R'+str(R_s),'3-проектируемый и эталонный на участке сопряжения прямой и кривой R'+str(R_kr)],shadow=True, fontsize=20, loc="lower left", ncol=1,bbox_to_anchor=(-0.0, -0.5),fancybox=True,borderaxespad=0.)
    st.pyplot(fig)
    
    # Сохраняем графики в папку с шаблонами
    fig_1 = gfiles_dir / "f1.png"
    fig_2 = gfiles_dir / "f2.png"
    fig.savefig(fig_1, dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Расчет прохождения горки
    X=np.arange(808,dtype=float).reshape(101,8)
    for i in range(8):
        X[:,i]=np.arange(101,dtype=float) + ([0, baza_tel, l, l+baza_tel, l+baza_tel/2+n+ne-baza_tel_e/2, l+baza_tel/2+n+ne-baza_tel_e/2+baza_tel_e, l+baza_tel/2+n+ne-baza_tel_e/2+baza_tel_e+le, l+baza_tel/2+n+ne-baza_tel_e/2+baza_tel_e+le+baza_tel_e])[i]
    T=h(X)
    S=np.zeros((101,3))
    S[:,0]=(T[:,2]+T[:,3])/2*(1+n/l)-n*(T[:,0]+T[:,1])/(2*l)
    S[:,1]=(T[:,4]+T[:,5])/2*(1+ne/le)-ne*(T[:,6]+T[:,7])/(2*le)
    S[:,2]=S[:,0]-S[:,1]
    maximum_gorka=np.abs(S[:,2]).max()
    usl1='Верно' if maximum_gorka<=(dh_dop-0.1) else 'Неверно'
    
    # Расчет прохождения аппарели
    Ta=ha(X,0,40)
    Sa=np.zeros((101,3))
    Sa[:,0]=(Ta[:,2]+Ta[:,3])/2*(1+n/l)-n*(Ta[:,0]+Ta[:,1])/(2*l)
    Sa[:,1]=(Ta[:,4]+Ta[:,5])/2*(1+ne/le)-ne*(Ta[:,6]+Ta[:,7])/(2*le)
    Sa[:,2]=Sa[:,0]-Sa[:,1]
    DS40=np.abs(Sa[:,2]).max()
    usl2='Верно' if DS40<=(dh_dop-0.1) else 'Неверно'
    
    u_min, u_max = 20, 50
    while np.abs(u_max-u_min)>0.0001:
        u_u=(u_min+u_max)/2
        Ta=ha(X,0,u_u)
        Sa[:,0]=(Ta[:,2]+Ta[:,3])/2*(1+n/l)-n*(Ta[:,0]+Ta[:,1])/(2*l)
        Sa[:,1]=(Ta[:,4]+Ta[:,5])/2*(1+ne/le)-ne*(Ta[:,6]+Ta[:,7])/(2*le)
        Sa[:,2]=Sa[:,0]-Sa[:,1]
        if np.abs(Sa[:,2]).max()>(dh_dop-0.1):
            u_max=u_u
        else:
            u_min=u_u
    maximum_apparel=np.abs(Sa[:,2]).max()
    usl3='Верно' if maximum_apparel<=(dh_dop-0.1) else 'Неверно'    
    
    fig2, ax2 = plt.subplots(figsize=(15, 10))
    ax2.set_xlabel(u'X, м', fontsize=20)
    ax2.set_ylabel(u'$\Delta$S, м', fontsize=20)
    ax2.grid(visible=True, which='both', color='k', linestyle='-', linewidth=1)
    ax2.tick_params(axis='both', which='major', width=1, labelsize=20)
    ax2.set_xlim([0, 100])
    ax2.plot(X[:,0], S[:,2], color='k', label='Горка')
    ax2.plot(X[:,0], Sa[:,2], color='k', linestyle="--", label='Аппарель')
    ax2.legend(fontsize=20)
    st.pyplot(fig2)
    fig2.savefig(fig_2, dpi=300, bbox_inches='tight')
    plt.close(fig2)

    # Проверка наличия шаблонов
    template_file_1 = gfiles_dir / "g_1.docx"
    template_file_2 = gfiles_dir / "g_2.docx"
    
    if not template_file_1.exists() or not template_file_2.exists():
        st.error(f"Ошибка: Шаблон не найден! Ожидался путь: {gfiles_dir}")
        st.stop()

    # Создаем объекты документов один раз
    doc_1 = DocxTemplate(template_file_1)
    doc_2 = DocxTemplate(template_file_2)

    if st.button("Сформировать и скачать отчеты"):
        try:
            context = {
                'IPADEZ':ipadez,'Rpadez':rpadez,'Model':model,'Number':number,
                'fio0': fio[0], 'fio1': fio[1], 'fio2': fio[2], 'fio3': fio[3], 'fio4': fio[4],
                'vl2':toFixed(l,3),'vlt2':toFixed(baza_tel,3),'vna':toFixed(na,3),'bstrih':toFixed(Bs,3),'vn':toFixed(n,3),'dh_dop':toFixed(dh_dop*1000,1),
                'ur1':toFixed(B_right,3),'Bavt':toFixed(B_left,3),'b0':toFixed(beta0,4),
                'alf1':toFixed(alfa[0],4),'alf1s':toFixed(alfas[0],4),'bet1':toFixed(beta[0],4),'bet1s':toFixed(betas[0],4),'gam1':toFixed(gama[0],4),
                'alf2':toFixed(alfa[1],4),'alf2s':toFixed(alfas[1],4),'bet2':toFixed(beta[1],4),'bet2s':toFixed(betas[1],4),'gam2':toFixed(gama[1],4),
                'alf3':toFixed(alfa[2],4),'alf3s':toFixed(alfas[2],4),'bet3':toFixed(beta[2],4),'bet3s':toFixed(betas[2],4),'gam3':toFixed(gama[2],4),
                'DSg':toFixed(maximum_gorka*1000,2),'M40Das':toFixed(DS40*1000,2),'MDas':toFixed(maximum_apparel*1000,2),'ukl':toFixed(u_u,2),
                'usl1':usl1,'usl2':usl2,'usl3':usl3,
                # Передаем массивы целиком (в шаблоне используйте цикл {% for i in range(101) %})
                's2g': [toFixed(val,4) for val in S[:,0]], 
                's3g': [toFixed(val,4) for val in S[:,1]], 
                'dsg': [toFixed(val,4) for val in S[:,2]],
                's2a': [toFixed(val,4) for val in Sa[:,0]], 
                's3a': [toFixed(val,4) for val in Sa[:,1]], 
                'dsa': [toFixed(val,4) for val in Sa[:,2]],
                'fig1': InlineImage(doc_1, str(fig_1), width=Mm(180), height=Mm(149)),
                'fig2': InlineImage(doc_1, str(fig_2), width=Mm(180), height=Mm(120))
            }
            
            context2 = context.copy()
            context2.update({
                'fig1': InlineImage(doc_2, str(fig_1), width=Mm(180), height=Mm(149)),
                'ln2':toFixed(l+n,3),
                'ymax':toFixed(maximum_gorka*1000,1), 
                'ymaxap':toFixed(maximum_apparel*1000,1)
            })
            
            # Расчет по нормам (для второго отчета)
            axles=4
            A=[-1.7, -1.8, -3.1]; B=[0.0, 13.5, 58.2]; C=[2.0, 0.8, -2.0]; D=[2.0,1.4,0.0]; E=[0.0, -80.4, -429.0]; F=[0.0, 13.5, 58.2]; G=[0.0, -0.6, -2.0]
            if typ_vag==2: A=[-4.0, -4.4, -6.0]; axles=6
            elif typ_vag==3: A[1:3]=[-7.5, -9.8]; axles=8
            jt = 0 if (l+n)<=11.8 else (1 if (l+n)<=14.7 else 2)
            context2.update({
                'axles':str(axles),'An':toFixed(A[jt],1),'Bn':toFixed(B[jt],1),'Cn':toFixed(C[jt],1),'Dn':toFixed(D[jt],1),'En':toFixed(E[jt],1),'Fn':toFixed(F[jt],1),'Gn':toFixed(G[jt],1)
            })
            
            doc_1.render(context)
            byte_io_1 = io.BytesIO()
            doc_1.save(byte_io_1)
            byte_io_1.seek(0)
            
            doc_2.render(context2)
            byte_io_2 = io.BytesIO()
            doc_2.save(byte_io_2)
            byte_io_2.seek(0)
            
            st.success("Данные внесены в шаблоны!")
            st.download_button( label="⬇️ Скачать РР6.docx",  data=byte_io_1, file_name=f"{number}_PP6.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document" )
            st.download_button( label="⬇️ Скачать РР11.docx", data=byte_io_2, file_name=f"{number}_PP11.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document" )
            
        except Exception as e:
            st.error(f"Произошла ошибка при генерации отчета: {e}")

# --- ВЫНЕСЕННЫЕ КНОПКИ --- 
#col_buttons, _ = st.columns([1, 1]) # Создаем колонку для кнопок 
#byte_io_1 = io.BytesIO()
#byte_io_2 = io.BytesIO()
#with col_buttons:
#    download_pp6 = st.download_button( label="⬇️ Скачать РР6.docx", data=byte_io_1, file_name=f"{number}_PP6.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="pp6_download" )
#    download_pp11 = st.download_button( label="⬇️ Скачать РР11.docx", data=byte_io_2, file_name=f"{number}_PP11.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="pp11_download" )