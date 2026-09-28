%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%  LaTeX class for preparing papers to "SPIIRAS Proceedings"
%%  (under MikTeX 2.9 platform)
%%  charset=utf8
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\NeedsTeXFormat{LaTeX2e}[1998/12/01]
\ProvidesClass{SPIIRAS_Proceedings}[2017/12/07 alpha v3.3
LaTeX class for preparing papers to "SPIIRAS Proceedings"]
\ClassWarningNoLine{SPIIRAS_Proceedings}{This class      MikTeX 2.9}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{extarticle}}
\let\if@openbib\iffalse
\DeclareOption{openbib}{\let\if@openbib\iftrue}

\ProcessOptions
\LoadClass[a5paper]{extarticle} 
\RequirePackage[T1,T2A]{fontenc} 
\RequirePackage[utf8]{inputenc} 
\RequirePackage[russian,english]{babel} 
\RequirePackage{mathptmx}
\RequirePackage{tempora}
\RequirePackage[reqno,tbtags]{amsmath} 
\RequirePackage{amsfonts,amssymb,mathrsfs} 
\RequirePackage{graphicx} 
\RequirePackage{cite} 
\RequirePackage{url} 
\RequirePackage{listings} 
\RequirePackage[font=small,format=plain,labelsep=period,justification=centering,skip=0pt]{caption}
\RequirePackage{verbatim} 
\RequirePackage{calc} 
\RequirePackage[colorlinks=true,linkcolor=black,urlcolor=blue,citecolor=black]{hyperref}
\RequirePackage{microtype} 
\RequirePackage{tabularx}
\RequirePackage[explicit]{titlesec} 
\RequirePackage{longtable} 
\RequirePackage{setspace} 
%///////////////////////////////////////////////////////%

% 108--170mm page margins

\oddsidemargin 0 mm
\textwidth 108 mm
\topmargin 0 mm
\headheight 0 mm
\headsep 0 mm
\textheight 170 mm
\footskip 7mm
\hoffset -5mm
\voffset -5mm

%///////////////////////////////////////////////////////%

% Дополнительные переменные для оформления статьи

\pdfpkresolution 5000 %полиграфическое качество печати
\parindent=1cm 
\pagestyle{empty} 
\tolerance 400 

\urlstyle{same} 

\clubpenalty=10000
\widowpenalty=10000
\singlespacing
\addto\captionsenglish{\renewcommand{\figurename}{Fig.}}
\renewcommand*{\citedash}{\hbox{-}\penalty\citepunctpenalty}


%///////////////////////////////////////////////////////%

% Листинги и Алгоритмы 
% far

\lstset{breaklines=true,language=C,showstringspaces=false,breaklines=true,xleftmargin=\parindent,captionpos=b,basicstyle=\fontsize{9pt}{10}\sffamily,basewidth=0.42em}

%///////////////////////////////////////////////////////%

%Перечни и Списки
\renewenvironment{itemize}%
      {\begin{list}{\nobreak--\hfil}{\setlength{\labelwidth}{0pt}
  \setlength{\labelsep}{5pt}
  \setlength{\leftmargin}{0pt}
  \setlength{\itemindent}{\parindent}
  \addtolength{\itemindent}{\labelwidth}
  \addtolength{\itemindent}{\labelsep}
  \setlength{\listparindent}{\parindent}
  \setlength{\itemsep}{0pt}
  \setlength{\parsep}{0mm}
  \setlength{\topsep}{0mm}
  \setlength{\partopsep}{0mm}}}{\end{list}}
 
\renewenvironment{enumerate}%
{	
	\begin{list}{\nobreak\strut\smash{\parbox[t]\labelwidth{\raggedright{\arabic{enumi}.}}}}
	{
		\setlength{\labelwidth}{0pt}
		\setlength{\leftmargin}{0pt}
		\setlength{\labelwidth}{\widthof{\arabic{enumi}.}}
		\setlength{\labelsep}{-5pt}		
		\setlength{\itemindent}{\parindent}
		%\addtolength{\itemindent}{\labelwidth}
		\addtolength{\itemindent}{10pt}
		\addtolength{\labelsep}{\labelwidth}
		\setlength{\listparindent}{\parindent}
		\setlength{\itemsep}{0pt}
		\setlength{\parsep}{0mm}
		\setlength{\topsep}{0mm}
		\setlength{\partopsep}{0mm}
		\usecounter{enumi}
	}
}{\end{list}} 


%///////////////////////////////////////////////////////%
%%  Сколь угодно жидкие строки
\sloppy

%%\setlength\parskip{2\p@ \@plus \p@}
\setlength\parskip{0pt}

%///////////////////////////////////////////////////////%

%%  Знаки нестрогих равенств (как принято у нас)
\def\le{\leqslant}
\def\leq{\leqslant}
\def\ge{\geqslant}
\def\geq{\geqslant}

%///////////////////////////////////////////////////////%

%%  Список литературы
\def\refnameRus{\normalsize \textbf{Литература}}
\def\refnameEng{\normalsize \textbf{References}}
\newcounter{aux@counter}
\def\thebibliographyRus#1{%
\refstepcounter{aux@counter}%
\vskip 8pt
\sectionBib*{\refnameRus}
\def\@biblabel##1{{\select@language{russian}##1.\hfill \hskip 0.45cm}}
\footnotesize
\list
 {
 \@biblabel{\arabic{enumi}}}{\settowidth\labelwidth{\@biblabel{#1}}\leftmargin\labelwidth
 \advance\leftmargin\labelsep
 \usecounter{enumi}}
 \setlength{\parskip}{-1pt}
 \def\newblock{\hskip .11em \@plus .33em \@minus .07em}%
 \sloppy\clubpenalty4000\widowpenalty4000
 \sfcode`\.=1000\relax
 \def\makelabel##1{\hfil ##1}
}

\def\thebibliographyEng#1{%
\refstepcounter{aux@counter}%
\vskip 8pt
\sectionBib*{\refnameEng}
\def\@biblabel##1{{\select@language{english}##1.\hfill \hskip 0.45cm}}
\footnotesize
\list
 {\@biblabel{\arabic{enumi}}}{\settowidth\labelwidth{\@biblabel{#1}}\leftmargin\labelwidth
 \advance\leftmargin\labelsep
 \usecounter{enumi}}
 \setlength{\parskip}{-1pt}
 \def\newblock{\hskip .11em \@plus .33em \@minus .07em}%
 \sloppy\clubpenalty4000\widowpenalty4000
 \sfcode`\.=1000\relax
 \def\makelabel##1{\hfil ##1}
}

%///////////////////////////////////////////////////////%

%%  Макросы для определения заголовка
%%  УДК
\def\udk#1{\gdef\@udk{#1}} %% УДК
%% DOI
\def\doi#1{\gdef\@doi{#1}} %% DOI
\global\let\@doi\@empty

%%  Авторы
\def\authorsTitleRus#1{\gdef\@authorsTitleRus{#1}} % авторы в заголовке на руском языке
\def\authorsTitleEng#1{\gdef\@authorsTitleEng{#1}} % авторы в заголовке на английском языке

\def\authorsRus#1{\gdef\@authorsRus{#1}} % авторы в тексте на русском языке
\def\authorsEng#1{\gdef\@authorsEng{#1}} % авторы в тексте на английском языке
%%  Название статьи
%\def\title#1{\gdef\@title{#1}} %% название статьи в заголовке
\def\titleRus#1{\gdef\@titleRus{#1}} %% название статьи на русском языке
\def\titleEng#1{\gdef\@titleEng{#1}} %% название статьи на английском языке
%%  Аннотация
\long\def\abstractRus#1{\gdef\@abstractRus{#1}} % текст аннотации на русском языке
\long\def\abstractEng#1{\gdef\@abstractEng{#1}} % текст аннотации на английском языке
%%  Ключевые слова
\def\keywordsRus#1{\gdef\@keywordsRus{#1}}% Ключевые слова на русском языке
\def\keywordsEng#1{\gdef\@keywordsEng{#1}} % Ключевые слова на английском языке

%///////////////////////////////////////////////////////%

\newcommand{\smallcapsfake}[1]{\fontsize{2.8mm}{5mm}\selectfont\expandafter\MakeUppercase\expandafter{#1} \normalsize\normalfont}

%%  Шапка
\renewcommand{\maketitle}{
\noindent\footnotesize\ifx\@doi\@empty\relax\else\hfill\footnotesize\textbf{DOI}~\@doi\fi%
\begin{center}
\normalsize\@authorsTitleRus\\%[3ex]
\normalsize\bfseries\MakeUppercase{\@titleRus}\\[8pt] %
\normalsize\normalfont
\end{center}
\rule{\textwidth}{0.5pt}
\textit{\@authorsRus}~\textbf{\@titleRus.}\\
{\hspace*{0.5cm}\textbf{Аннотация.}}~{\hyphenpenalty=10000\setlength{\parindent}{0.5cm} \@abstractRus}\\
%\textbf{Ключевые слова:}~\@keywordsRus \\[-4pt] %
\hspace{-\parindent}\hspace*{0.5cm}\textbf{Ключевые слова:}~\@keywordsRus \\[-4pt] % %% some magic to make
\rule{\textwidth}{0.5pt} \\[-2pt] %
}

\newcommand{\makeengtitle}{
\noindent\footnotesize\textbf{UDK}~\@udk\ifx\@doi\@empty\relax\else\hfill\footnotesize\textbf{DOI}~\@doi\fi
\begin{center}
    \normalsize{\scshape\@authorsTitleEng}\\%[3ex]
    \normalsize\bfseries\MakeUppercase{\@titleEng}\\[8pt] %
    \normalsize\normalfont
\end{center}
\rule{\textwidth}{0.5pt}
\textit{\@authorsEng}~\textbf{\@titleEng.}\\
{\hspace*{0.5cm}\textbf{Abstract.}}~{\hyphenpenalty=10000\setlength{\parindent}{0.5cm} \@abstractEng}\par
\hspace{-\parindent}\hspace*{0.5cm}\textbf{Keywords:}~\@keywordsEng \\[-4pt] % %% some magic to make last abstract paragraph look good 
\rule{\textwidth}{0.5pt} \\[-2pt] %
}

%///////////////////////////////////////////////////////%

%%  Информация об Авторах
\newenvironment{aboutAuthors}{\vskip 4pt\parindent=0pt\footnotesize}{}
\newenvironment{aboutAuthorsRus}{\vskip 4pt\parindent=0pt\footnotesize}{} 
%///////////////////////////////////////////////////////%

%%  Реферат и Summary

\long\def\summaryRus#1{\long\gdef\@summaryRus{#1}}% Реферат на русском языке
\long\def\summaryEng#1{\long\gdef\@summaryEng{#1}} % Реферат на английском языке
\newlength{\summaryRusLenght}
\newlength{\summaryEngLenght}
\newlength{\halfoftextheight}
\halfoftextheight=0.45\textheight

\newcommand{\makeSummary}{
\settoheight{\summaryRusLenght}{\vbox{\@summaryRus}}
\settoheight{\summaryEngLenght}{\vbox{\@summaryEng}}
\newpage
\begin{center}
\normalsize\textbf{РЕФЕРАТ}\\[8pt] %
\normalsize\normalfont
\end{center}
\normalsize
\textit{\@authorsRus}~\textbf{\@titleRus.}\\[-10pt] %
\small\@summaryRus
\ifnum \summaryRusLenght>\halfoftextheight
	\newpage	
\fi
%\ifnum \summaryRusLenght<\halfoftextheight
%	\ifnum \summaryEngLenght<\halfoftextheight
%		\\
%	\fi
%\else
%\newpage
%\fi
\begin{center}
\normalsize\textbf{SUMMARY}\\[8pt] %
\normalsize\normalfont
\end{center}
\normalsize
\textit{\@authorsEng}~\textbf{\@titleEng.}\\[-10pt] %
\small\@summaryEng
}

%///////////////////////////////////////////////////////%

%%  Точки после номеров теорем
\def\afterthmseparator{.}
\def\@begintheorem#1#2{%
\setlength{\topsep}{1pt}%
\setlength{\partopsep}{0mm}%
\trivlist\item[\hskip\labelsep{\rm
#1\ #2\unskip\afterthmseparator}]\itshape}
\def\@opargbegintheorem#1#2#3{%
\setlength{\topsep}{1pt}%
\setlength{\partopsep}{0mm}%
\trivlist\item[\hskip\labelsep{\rm
#1\ #2\ {\rm{#3}}\afterthmseparator}]\ditshape}

%///////////////////////////////////////////////////////%

%%  Раздел
\newcommand\sectionBib{\@startsection{sectionBib}{1}{\parindent}%
{0pt}%
{0pt}%
{\normalfont\normalsize\bfseries}}


\titleformat{\section}[block]{\normalfont\normalsize\bfseries}{\thesection.}{.5em}
{\normalfont\normalsize\bfseries#1}
\titlespacing{\section}
{\parindent}{8pt plus 2pt minus 2pt}{4pt plus 1pt minus 1pt}

%///////////////////////////////////////////////////////%
%%  Подраздел
%\renewcommand\subsection{\@startsection{subsection}{2}{\parindent}%
%{18\p@ \@plus 4\p@ \@minus 4\p@}%
%{4\p@ \@plus 2\p@ \@minus 1\p@}%
%{\normalfont\normalsize\center\itshape}}

\titleformat{\subsection}[runin]{\normalfont\normalsize\bfseries}{\thesubsection.}{.5em}
{\normalfont\normalsize\bfseries#1}[.\;]
\titlespacing{\subsection}
{\parindent}{0pt}{0pt}

%///////////////////////////////////////////////////////%
%% Подподраздел
\titleformat{\subsubsection}[runin]{\normalfont\normalsize\bfseries}{\thesubsubsection.}{.5em}
{\normalfont\normalsize\bfseries#1}[.\;]
\titlespacing{\subsubsection}
{\parindent}{0pt}{0pt}

%///////////////////////////////////////////////////////%

\newtheorem{theorem}{\hspace{\parindent}\sl{Theorem,}}
\newtheorem{corollary}{\hspace{\parindent}\sl{Corollary,}}
\newtheorem{lemma}{\hspace{\parindent}\sl{Lemma,}}
\newtheorem{statement}{\hspace{\parindent}\sl{Statement,}}
\newtheorem{proposition}{\hspace{\parindent}\sl{Proposition,}}
\newtheorem{definition}{\hspace{\parindent}\sl{Definition,}}
\newtheorem{problem}{\hspace{\parindent}\sl{Problem,}}

%%  Доказательство
\newenvironment{proof}
{\vspace{1pt}\par{\sl%
Proof}}%
{\noindent\vspace{1pt}}

%%  Доказательство теоремы
\newenvironment{proofoftheorem}[1]
{\vspace{1pt}\par{\sl%
Proof of theorem, #1.}}%
{\noindent\vspace{1pt}}

%%  Доказательство следствия
\newenvironment{proofofcorollary}[1]
{\vspace{1pt}\par{\sl%
Proof of collary, #1.}}%
{\noindent\vspace{1pt}}

%%  Доказательство леммы
\newenvironment{proofoflemma}[1]
{\vspace{1pt}\par{\sl%
Proof of lemma, #1.}}%
{\noindent\vspace{1pt}}

%%  Доказательство утверждения
\newenvironment{proofofstatement}[1]
{\vspace{1pt}\par{\sl%
Proof of statement, #1.}}%
{\noindent\vspace{1pt}}

%%  Доказательство предложения
\newenvironment{proofofproposition}[1]
{\vspace{1pt}\par{\sl%
Proof of proposition, #1.}}%
{\noindent\vspace{1pt}}

%%  Алгоритм
\newtheorem{alg}{\hspace{\parindent}\sl{Algorithm}}%
\newenvironment{algorithm}[1][\unskip]{\begin{alg}[#1]\em}{\end{alg}}%
\def\thealgorithm{\thealg}

%%  Замечание
\newtheorem{rem}{\hspace{\parindent}\sl{Remark,}}%
\newenvironment{remark}[1][\unskip]{\begin{rem}[#1]\em}{\end{rem}}%
\def\theremark{\therem}

%%  Пример
\newtheorem{exmpl}{\hspace{\parindent}\sl{Example,}}%
\newenvironment{example}[1][\unskip]{\begin{exmpl}[#1]\em}{\end{exmpl}}%
\def\theexample{\theexmpl}


%%  Ссылка на элемент перечня
\def\itemref#1{{\rm\ref{#1})}}

%%  В окружении multline сдвиг=0
\multlinegap=0pt



\hyphenation{SPIIRAS}

\endinput
