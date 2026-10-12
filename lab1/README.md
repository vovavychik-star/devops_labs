# Лабораторная №2(1) Полный мониторинг маленького сервиса

# Начало работы

# Вступление

Для начала нужно разобраться с какими инструментами мне предстоит работать. Я захотел поставить себе на свою машину Grafan'у, причем web. Устанавлю на macos через brew, это очень удобно.



![](assets/yNQ6ieqKjGzF6kHYi7n4sRfd85xzDG9z0zdCcG_UDmE=.png)

Зайдем на localhost и начнем настройку



![](assets/19wJj8LkxQX32HQrMltTgM_zB1bJGzEI0eVyVon4Cbo=.png)

Еще необходимо установить агента, который будет собирать метрики, а также БД, гугл предложил прометеус, поэтому его и возьмем

![](assets/FMK3Np-cYkLoR_vsUmd_dmmNHsXRd3tOuAVoiLZHxAE=.png)

Все, теперь в веб интерфейсе начнем настройку, создадим connection, пропишем api прометеуса, запустим в фоновом режиме сервисы node explorer и сам prometheus.



![](assets/50MpAGBAy_hZUdFbtgdeVATvNgiCtqSGhAOnYyio2q8=.png)



![](assets/1FK_TDyCcfMHZrJpmKQX7PE_edPs9sNKzQW6H6YI_Ig=.png)

А, ну еще надо подкорректировать yml файл, чтобы node explorer понимал, что ему можно брать дату ПК и перекидывать на мой локалхост



![](assets/DjwRX2JkYFl9gDrMx51_u9s0VZVyJ1t_lQJ5uAOwDZw=.png)

Теперь успешно показывает дашборд, который смотрит загруженность CPU.

## Основная работа

Теперь приступим к собственному сервису, настроим для него анализ логов и метрик.

Подготовка:



![](assets/_i8EUEuCmyjgZd2z-jd3HBT9WaDsmgw7ACwiVdTQ-ko=.png)

Создадим docker файл,  который будет задавать все необходимые данные: сервис, на каком порте он будет работать, на какой версии питона и другие вспомогательные файлы в одну единую директорию.



![](assets/xLJeO2DerTGc3NxKHptauJyMRc5EhWLNOIu3qMPmr8k=.png)

Теперь соберем докер контейнер и запустим его: подтянем grafan, prometheus и jaeger(для трейсов), promtail(для логов), alertmanager.

Теперь это все надо обьединить в единое целое:



![](assets/kojNP2VPAD2z3b66waYfJjZwapoDiV7QGaoGRPI-Me8=.png)

Посмотрим процесс статус

![](assets/ljzP89k2SOMDetYYy-R1HYtIXvmh4ZVnzmsUBGTMAVY=.png)

## Grafana

![](assets/LbqW7heIJxLFdhnmAT2pUG5nyZjsMXfC9z2ehFYbsPI=.png)

График интенсивности:

![](assets/Ge5TTdLZ_M65yHaxa8bPvDmduRSkuEUrSJ9YH0qJi-o=.png)

Доля ошибок:

![](assets/1XFaGDlL9IHDK4f0Wsg9FcUG7w402434K5fhXTFbYE0=.png)

Задержка:





![](assets/UcSFihmZyrq7dGccfsHTPKBCmVh-0VXva6r5VOmhRhw=.png)

## Jaeger

##

![](assets/VzcH7a-3mBJTgvAEfjR-NW2mYx7QMZZjtb7aJaejhdU=.png)



![](assets/c4BgPt4k9rV2NkeoV3RGgAB1oiV61zzRNeH8WLwQlDM=.png)



![](assets/uk6dJ-tWlJWWP9SiJcOL-bRm8GcbLJP0CivMtT6Y4Rc=.png)

/error. Тут мы смотрим где именно произошла ошибка, на какой из цепочек спана действия пользователя

![](assets/zLhojEnIYFjknf3GO9Kl6WGLzawIOcRVV-L49wS8Oq4=.png)

При помощи различных операций мы можем понять корень проблемы, понять в чем дело, начать дебаггинг и прийти к оптимизорованной работе запросов-ответов.

## AlertManager

Посмотрим метрики в Prometheus. Далее уже посмотрим карточки с алертами в alert manager

![](assets/VJXi_bUAGQ5i4jlEQmaM4Gm_mMTD28_MIsKmcqUaH8U=.png)



![](assets/MRTf1E3mZmxWtADdfWyFR5j0Jza-KWNrEDPjgy5HQxc=.png)

Как я понял, alert manager используют как доску с уведомлениями, на которые откликаются, выполнив или поставив на задачу ту или иную ошибку. Можно замутить, отфильтровать, откнинуться на источник проблемы прямиком в логи



Выводы
------

Теперь я понимаю как работать с ошибками на сервисе сервере, какие есть полезные инструменты, чтобы найти ошибку -> по метрикам понять что сломалось -> по логам как и во сколько и в каком размере(спан) -> поставить на учет -> пофиксить проблему
