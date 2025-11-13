# Benfica Multi-Sport Calendar Hub

> 🇵🇹 Em Português de seguida

> 🇬🇧 English further down

---

## 🇵🇹 Português

### 🎯 Objetivo

O **Benfica Multi-Sport Calendar Hub** é um projeto pessoal, para desenvolver uma plataforma completa (parser, API, frontend web e app mobile), para **centralizar todos os jogos do Sport Lisboa e Benfica**, e oferecer aos users funcionalidades que o SL Benfica e Benfica SAD não disponibilizam.

Eventos considerados:
- ⚽ Futebol Masculino (A, B, Sub-23, Sub-19)
- ⚽ Futebol Feminino (A)
- 👟 Futsal (F/M)
- 🤾 Andebol (F/M)
- 🏀 Basquetebol (F/M)
- 🏐 Voleibol (F/M)
- 🏑 Hóquei em Patins (F/M)
- 🏛️ Museu Cosme Damião
- _🎫 Bilhética (eventualmente)_

O objetivo principal é simples:

> **Dar às modalidades e formação do futebol o destaque e visibilidade que merecem**, tentando aproximar os adeptos das equipas, utilizando estratégias que o clube não utiliza.

- Este projeto é **independente**, de um adepto para adeptos
- Nenhum outro website/app junta **todas** as modalidades num só sítio (segundo o meu conhecimento)
- Incentiva ida aos pavilhões
- Foco em usabilidade, clareza, e proximidade com os adeptos
- 100% gratuito e open-source

A app permitirá:
- Ver os próximos jogos por modalidade (já disponível por vias oficiais)
- Filtrar por género, modalidade ou escalão (já disponível por vias oficiais, não intuitivo, e vistas singulares por modalidade)
- Criar alertas pessoais
- Ver os próximos jogos perto da tua zona (geo-filtragem)
- Aceder rapidamente a bilhetes ou transmissões (mediante disponibilização oficial)
- Calendário completo numa única interface

---

## 📖📏 Arquitetura

O projeto é composto por **3 grandes componentes**:

### 1) 🧩 _ECAL Parser_ (Python)

- Download automático do [calendário oficial](https://benfica.ecal.com/) em formato ICS
- Normalização dos eventos em JSON
- Deteção:
  - Modalidade
  - Género
  - Equipa/Escalão (se aplicável)
  - Competição
  - Jornada
  - Adversário
  - Local
  - Jogo casa/fora
- Extração de links úteis


---

### 2) 🌐 _API_ (FastAPI + PostgreSQL, talvez)

> Arquitetura para este módulo não finalizada, sujeito a alterações

A API será responśavel por:

- Servir o calendário completo via REST/JSON
- Endpoints públicos:
  - `/games`
  - `/games/{sport}`
  - `/games/today`  
  - `/games/near?lat=X&lon=Y`  
  - `/sports`  
  - `/teams`  
- Suporte para caching (Redis opcional)  
- Ponto central de dados para:
  - Website  
  - Apps móveis  
  - Widgets externos  
  - Automação (ex.: bots Discord)

---

### 3) 🎨 Frontend + 📱 App

> Arquitetura para este módulo não finalizada, sujeito a alterações

#### 🌐 Web App (React / Next.js)

- Calendário Visual
- Filtros por modalidade, género e competição
- Mapa com os jogos por perto
- Página do jogo com:
  - Localização
  - Info de bilhetes
  - Info de transmissão
  - Links úteis
- Layout mobile-first

#### 📱 App Android e iOS (Flutter ou React Native)

- Notificações Push (incluindo os jogos perto)
- Favoritos
- Modo escuro (naturalmente)
- Navegação por modalidade


## 📚 Stack Tecnológica

### Backend
- Python
- FastAPI
- PostgreSQL + SQLAlchemy
- Redis
- icalendar, python-dateutil
- Docker (deploys)

### Web Frontend
- React / Next.js
- TailwindCSS
- Mapbox/Leaflet para o mapa
- Vercel (host)

### Mobile Frontend
- Flutter **ou** React Native
- Firebase Cloud Messaging
- Expo (caso React Native)

---

## 🇬🇧 English

### 🎯 Objective

The **Benfica Multi-Sport Calendar Hub** is a personal project to develop a complete platform (parser, API, web frontend, and mobile app) that **centralizes all Sport Lisboa & Benfica's events** and provide users with features SL Benfica and Benfica SAD currently do not offer.

Events included:
- ⚽ Men’s Football (A, B, U23, U19)
- ⚽ Women’s Football (A)
- 👟 Futsal (M/F)
- 🤾 Handball (M/F)
- 🏀 Basketball (M/F)
- 🏐 Volleyball (M/F)
- 🏑 Roller Hockey (M/F)
- 🏛️ Cosme Damião Museum events
- _🎫 Ticketing (eventually)_

Main goal:

> **Give Benfica’s sports sections and youth teams the visibility they deserve**, closing the gap between supporters and the various squads.

This project is:
- **Independent**, from a fan to fans  
- (As far as I know) the only platform putting **all** Benfica sports together  
- Encouraging arena attendance  
- Focused on usability, clarity, and fan experience  
- Fully free and 100% open-source

The app will allow users to:
- View upcoming matches by sport  
- Filter by gender, sport, or squad  
- Create personal alerts  
- See matches happening near them (geo-filtering)  
- Quickly access ticketing or broadcast info  
- Browse the full calendar in a single interface  

---

## 📖📏 Architecture

Built around **3 main components**:

---

### 1) 🧩 ECAL Parser (Python)

- Automatic download of the official ICS calendar  
- Parsing and normalization into JSON  
- Detection of:
  - Sport  
  - Gender  
  - Team/Squad  
  - Competition  
  - Matchday  
  - Opponent  
  - Venue  
  - Home/Away  
- Extraction of useful links  

---

### 2) 🌐 API (FastAPI + PostgreSQL, potentially)

> Architecture not final yet, subject to changes.

Responsible for:

- Serving the complete calendar through REST/JSON  
- Planned endpoints:
  - `/games`
  - `/games/{sport}`
  - `/games/today`
  - `/games/near?lat=X&lon=Y`
  - `/sports`
  - `/teams`
- Optional caching via Redis  
- Central data source for:
  - Website  
  - Mobile apps  
  - Widgets  
  - Bots (e.g. Discord)

---

### 3) 🎨 Frontend + 📱 Mobile App

> Architecture not final yet, subject to changes.

#### 🌐 Web App (React / Next.js)

- Visual calendar  
- Filters by sport, gender, and competition  
- Map with nearby matches  
- Match detail page with:
  - Location  
  - Ticketing  
  - Broadcast info  
  - Useful links  
- Mobile-first layout  

#### 📱 Android & iOS App (Flutter or React Native)

- Push notifications  
- Favourites  
- Dark mode  
- Sport-based navigation  

---

## 📚 Tech Stack

### Backend
- Python  
- FastAPI  
- PostgreSQL + SQLAlchemy  
- Redis  
- icalendar, python-dateutil  
- Docker  

### Web Frontend
- React / Next.js  
- TailwindCSS  
- Mapbox/Leaflet  
- Vercel  

### Mobile Frontend
- Flutter **or** React Native  
- Firebase Cloud Messaging  
- Expo (if React Native)
