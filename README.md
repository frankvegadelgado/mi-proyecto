# Full Stack Hello World
### Vue 3 + TypeScript + Vite + Pinia + Vue Router + Axios + FastAPI + SQLAlchemy + SQLite

---

## Tabla de Contenidos

1. [Estructura del proyecto](#1-estructura-del-proyecto)
2. [Instalación desde cero](#2-instalación-desde-cero)
   - [Requisitos previos](#requisitos-previos)
   - [Backend](#backend)
   - [Frontend](#frontend)
3. [Levantar el proyecto](#3-levantar-el-proyecto)
4. [Guía conceptual](#4-guía-conceptual)
   - [Las dos grandes partes](#las-dos-grandes-partes)
   - [Backend — cada tecnología](#backend--cada-tecnología)
   - [Frontend — cada tecnología](#frontend--cada-tecnología)
   - [Cómo se comunican](#cómo-se-comunican)
5. [El código capa por capa](#5-el-código-capa-por-capa)
   - [El viaje completo de un click](#el-viaje-completo-de-un-click)
   - [1. Vite — El punto de entrada](#1-vite--el-punto-de-entrada)
   - [2. Vue Router — El que decide qué mostrar](#2-vue-router--el-que-decide-qué-mostrar)
   - [3. Vue 3 — El que dibuja la pantalla](#3-vue-3--el-que-dibuja-la-pantalla)
   - [4. TypeScript — El que valida los tipos](#4-typescript--el-que-valida-los-tipos)
   - [5. Pinia — El almacén central](#5-pinia--el-almacén-central)
   - [6. Axios — El mensajero](#6-axios--el-mensajero)
   - [7. FastAPI — El portero del servidor](#7-fastapi--el-portero-del-servidor)
   - [8. Pydantic — El validador](#8-pydantic--el-validador)
   - [9. SQLAlchemy — El traductor](#9-sqlalchemy--el-traductor)
   - [10. SQLite — El archivo que guarda todo](#10-sqlite--el-archivo-que-guarda-todo)
6. [El código completo](#6-el-código-completo)
   - [Backend](#backend-1)
   - [Frontend](#frontend-1)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Estructura del proyecto

```
mi-proyecto/
├── backend/
│   ├── main.py           ← App principal FastAPI + rutas
│   ├── database.py       ← Conexión a SQLite
│   ├── models.py         ← Modelos de la base de datos
│   ├── schemas.py        ← Validación Pydantic
│   └── requirements.txt  ← Dependencias Python
└── frontend/
    └── src/
        ├── main.ts           ← Arranque de la app
        ├── App.vue           ← Componente raíz + navegación
        ├── router/
        │   └── index.ts      ← Definición de rutas
        ├── stores/
        │   ├── helloStore.ts ← Store del Hello World
        │   └── itemsStore.ts ← Store de Items (DB)
        ├── views/
        │   ├── HomeView.vue  ← Página /
        │   └── ItemsView.vue ← Página /items
        └── api/
            └── axios.ts      ← Cliente HTTP centralizado
```

---

## 2. Instalación desde cero

### Requisitos previos

| Herramienta | Versión mínima | Verificar con |
|---|---|---|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

---

### Backend

#### 1. Crear la estructura de carpetas

```bash
mkdir mi-proyecto && cd mi-proyecto
mkdir backend && cd backend
```

#### 2. Crear y activar el entorno virtual

```bash
python -m venv venv

# Mac / Linux
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\activate
```

> Sabrás que está activo cuando ves `(venv)` al inicio del prompt.

#### 3. Instalar dependencias

```bash
pip install fastapi uvicorn sqlalchemy pydantic
```

#### 4. Crear `requirements.txt`

```bash
pip freeze > requirements.txt
```

> Para instalar en otro entorno: `pip install -r requirements.txt`

---

### Frontend

#### 1. Crear el proyecto con Vite

```bash
cd ..  # volver a mi-proyecto/
npm create vite@latest frontend -- --template vue-ts
cd frontend
```

#### 2. Instalar dependencias base

```bash
npm install
```

#### 3. Instalar librerías adicionales

```bash
npm install pinia vue-router axios
```

#### 4. Verificar que todo esté instalado

```bash
npm list pinia vue-router axios
```

---

## 3. Levantar el proyecto

Necesitas **dos terminales abiertas** al mismo tiempo:

| Terminal | Directorio | Comando |
|---|---|---|
| Terminal 1 — Backend | `mi-proyecto/backend/` | `uvicorn main:app --reload` |
| Terminal 2 — Frontend | `mi-proyecto/frontend/` | `npm run dev` |

Una vez levantado:

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **Documentación automática:** http://localhost:8000/docs

---

## 4. Guía conceptual

### Las dos grandes partes

El proyecto está dividido en dos mundos que se comunican por red:

- **Frontend** — lo que ve y toca el usuario. Corre en el navegador del usuario.
- **Backend** — el servidor. Corre en tu máquina o en la nube. Maneja datos y lógica de negocio.

El frontend y el backend **solo se hablan por HTTP con JSON**. No saben nada el uno del otro más allá de eso. Esto significa que podrías reemplazar el frontend por una app móvil, o el backend por Node.js, y el otro lado no se enteraría.

---

### Backend — cada tecnología

**FastAPI**
Es el framework de Python que recibe peticiones HTTP y devuelve respuestas JSON. Es el "portero" del servidor. Lo que lo hace especial es que genera documentación automática en `/docs` y es extremadamente rápido.

**Pydantic**
Es la capa de validación. Cuando el frontend manda datos, Pydantic verifica que vengan en el formato correcto antes de tocar la base de datos. Si falta un campo o el tipo es incorrecto, rechaza la petición automáticamente.

**SQLAlchemy**
Es el ORM (Object Relational Mapper) — el intermediario entre Python y la base de datos. En lugar de escribir SQL crudo, escribes Python y SQLAlchemy lo traduce al SQL correcto.

**SQLite**
Es la base de datos en sí. Es un archivo `.db` que vive en tu disco. No necesita instalación ni servidor separado, por eso es perfecta para desarrollo. En producción se reemplaza fácilmente por PostgreSQL sin cambiar casi nada del código.

---

### Frontend — cada tecnología

**Vite**
Es la herramienta de construcción. Toma todos tus archivos `.vue`, `.ts`, imágenes, etc., y los convierte en algo que el navegador entiende. Durante desarrollo, tiene hot reload — los cambios se ven al instante sin recargar la página.

**Vue 3**
Es el framework de interfaz. Su concepto central es que la UI es **reactiva**: cuando un dato cambia, la pantalla se actualiza sola automáticamente. No tienes que decirle "actualiza este texto", simplemente cambias el dato y Vue se encarga.

**TypeScript**
Es JavaScript con tipos. Permite que VS Code avise de errores antes de correr el código, como si tuvieras un asistente revisando tu trabajo en tiempo real. No aparece en el navegador — solo existe mientras desarrollas.

**Vue Router**
Maneja la navegación entre páginas. Una app Vue es en realidad una sola página HTML (SPA). Vue Router simula múltiples páginas cambiando lo que se muestra según la URL, sin recargar el navegador.

**Pinia**
Es el almacén central de datos del frontend. Resuelve el problema de: "¿dónde viven los datos que múltiples componentes necesitan?" Cada store agrupa datos de un dominio específico (uno para el usuario, otro para los items, etc.).

**Axios**
Es el cliente HTTP — el mensajero entre el frontend y el backend. Hace las peticiones al servidor y trae las respuestas. Lo que lo hace mejor que `fetch` nativo es que permite configurar URL base, headers de autenticación, y manejo de errores en un solo lugar.

---

### Cómo se comunican

```
[NAVEGADOR]                          [SERVIDOR]

Vue 3        ←→  Pinia  ←→  Axios  ←→  FastAPI  ←→  Pydantic  ←→  SQLAlchemy  ←→  SQLite
(pantalla)      (datos)   (HTTP)       (rutas)      (validar)      (traducir)       (DB)
```

---

## 5. El código capa por capa

### El viaje completo de un click

Cuando el usuario entra a `/items` y agrega un item nuevo, esto es lo que ocurre exactamente:

```
[Usuario hace click en "Agregar"]
        ↓
ItemsView.vue  →  handleSubmit()          Vue detecta el evento del formulario
        ↓
itemsStore.ts  →  createItem(payload)     Pinia ejecuta la acción
        ↓
axios.ts       →  api.post('/items', ...) Axios sale del navegador hacia la red
        ↓
main.py        →  @app.post("/api/items") FastAPI recibe la petición
        ↓
schemas.py     →  ItemCreate valida       Pydantic verifica que los datos son correctos
        ↓
models.py      →  Item() + db.add()       SQLAlchemy traduce a SQL
        ↓
hello.db       →  INSERT INTO items...    SQLite guarda en el archivo
        ↑
schemas.py     →  ItemResponse serializa  Pydantic formatea la respuesta
        ↑
main.py        →  return JSON             FastAPI responde al frontend
        ↑
axios.ts       →  res.data               Axios recibe y parsea la respuesta
        ↑
itemsStore.ts  →  items.value.push()     Pinia actualiza el state
        ↑
ItemsView.vue  →  v-for re-dibuja        Vue actualiza la pantalla automáticamente
```

---

### 1. Vite — El punto de entrada

Vite no aparece en el código directamente — trabaja por debajo compilando todo. Su trabajo comienza cuando ejecutas `npm run dev`. El primer archivo que procesa es `main.ts`.

```typescript
// frontend/src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

const app = createApp(App)
app.use(createPinia())   // registra Pinia globalmente
app.use(router)          // registra Vue Router globalmente
app.mount('#app')        // conecta Vue al <div id="app"> del HTML
```

**Qué hace cada línea:**
- `createApp(App)` — crea la instancia de Vue usando `App.vue` como raíz
- `app.use(createPinia())` — hace que cualquier componente pueda acceder a los stores
- `app.use(router)` — hace que `<RouterView>` y `<RouterLink>` funcionen en toda la app
- `app.mount('#app')` — Vue toma control del `<div id="app">` en el HTML

---

### 2. Vue Router — El que decide qué mostrar

```typescript
// frontend/src/router/index.ts
const routes = [
  { path: '/',       component: HomeView  },
  { path: '/items',  component: ItemsView },
]

const router = createRouter({
  history: createWebHistory(),  // URLs limpias sin # (ej: /items en vez de /#/items)
  routes,
})
```

```vue
<!-- frontend/src/App.vue -->
<nav>
  <RouterLink to="/">Home</RouterLink>
  <RouterLink to="/items">Items</RouterLink>
</nav>

<RouterView />
```

**Qué hace cada parte:**
- `routes` — es el mapa: "si la URL es X, muestra el componente Y"
- `createWebHistory()` — usa la API del navegador para URLs limpias sin `#`
- `<RouterLink>` — genera un `<a>` que cambia la URL sin recargar la página
- `<RouterView>` — es el "hueco" donde Vue Router inyecta el componente según la URL. Cuando estás en `/items`, aquí aparece `ItemsView.vue`

---

### 3. Vue 3 — El que dibuja la pantalla

```vue
<!-- frontend/src/views/ItemsView.vue -->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useItemsStore } from '../stores/itemsStore'

const store = useItemsStore()        // conecta con el store de Pinia
const newName = ref('')              // dato reactivo local — si cambia, la UI cambia

onMounted(() => store.fetchItems())  // Vue llama esto cuando el componente aparece

async function handleSubmit() {
  if (!newName.value.trim()) return
  await store.createItem({ name: newName.value, description: newDescription.value })
  newName.value = ''                 // limpiar el input — Vue actualiza el <input> solo
}
</script>

<template>
  <p v-if="store.loading">Cargando...</p>               <!-- muestra si loading es true -->
  <p v-else-if="store.error">❌ {{ store.error }}</p>   <!-- muestra si hay error -->
  <ul v-else>
    <li v-for="item in store.items" :key="item.id">     <!-- repite por cada item -->
      {{ item.name }}
    </li>
  </ul>
</template>
```

**Qué hace cada parte:**
- `ref('')` — crea un dato reactivo. Cuando cambia `newName.value`, Vue actualiza el `<input>` vinculado
- `onMounted()` — hook de ciclo de vida. Vue lo llama automáticamente cuando el componente aparece en pantalla
- `v-if / v-else-if / v-else` — renderizado condicional según el estado del store
- `v-for` — Vue repite el `<li>` por cada objeto en `store.items`. Cuando el array cambia, Vue actualiza la lista automáticamente
- `{{ }}` — interpolación: Vue escribe el valor de la variable en el HTML

---

### 4. TypeScript — El que valida los tipos

TypeScript actúa en todos los archivos `.ts` y en los `<script setup lang="ts">`. Su trabajo es silencioso pero constante — avisa de errores en VS Code antes de correr el código.

```typescript
// frontend/src/stores/itemsStore.ts

// Define la "forma" exacta que debe tener un Item
interface Item {
  id: number
  name: string
  description: string
}

// Define qué necesitas para crear un Item (sin id, porque lo genera la DB)
interface ItemCreate {
  name: string
  description: string
}

const items = ref<Item[]>([])      // TypeScript sabe: array de Items, no de cualquier cosa
const loading = ref<boolean>(false) // TypeScript sabe: solo true o false

async function createItem(payload: ItemCreate) {  // TypeScript verifica que payload tenga name y description
  const res = await api.post<Item>('/items', payload)  // TypeScript sabe que res.data es un Item
  items.value.push(res.data)
}
```

**Por qué importa:** si en `ItemsView.vue` intentas acceder a `item.precio` (que no existe en la interfaz), TypeScript te muestra un error rojo en VS Code antes de que corras el código. Sin TypeScript, ese error solo aparecería en el navegador en tiempo de ejecución.

---

### 5. Pinia — El almacén central

Pinia tiene dos stores en este proyecto, cada uno responsable de su propio dominio:

```typescript
// frontend/src/stores/helloStore.ts — dominio: mensaje del servidor
export const useHelloStore = defineStore('hello', () => {
  const data = ref<HelloResponse | null>(null)  // STATE: el dato
  const loading = ref(false)

  async function fetchHello() {                  // ACTION: la lógica
    loading.value = true
    const res = await api.get<HelloResponse>('/hello')
    data.value = res.data
    loading.value = false
  }

  return { data, loading, fetchHello }          // expone al exterior
})
```

```typescript
// frontend/src/stores/itemsStore.ts — dominio: items de la DB
export const useItemsStore = defineStore('items', () => {
  const items = ref<Item[]>([])

  async function fetchItems() {
    const res = await api.get<Item[]>('/items')
    items.value = res.data                       // Vue re-renderiza todo lo que use items
  }

  async function createItem(payload: ItemCreate) {
    const res = await api.post<Item>('/items', payload)
    items.value.push(res.data)                   // actualiza el state local sin re-fetch
  }

  return { items, loading, error, fetchItems, createItem }
})
```

**Por qué dos stores:**
- `helloStore` — responsable solo del mensaje de bienvenida del servidor
- `itemsStore` — responsable solo de la lista de items y operaciones CRUD
- Si mañana agregas usuarios, creas `userStore`. Cada dominio, su propio store

**La magia de Pinia:** cuando `items.value` cambia en el store, **todos** los componentes que usen `store.items` se actualizan automáticamente. No tienes que emitir eventos ni pasar props.

---

### 6. Axios — El mensajero

```typescript
// frontend/src/api/axios.ts
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',  // URL base — se antepone a todas las peticiones
  headers: {
    'Content-Type': 'application/json',  // le dice al servidor que mandamos JSON
  },
})

export default api
```

```typescript
// Uso en los stores:
api.get('/hello')
// → GET http://localhost:8000/api/hello

api.get('/items')
// → GET http://localhost:8000/api/items

api.post('/items', { name: 'Ejemplo', description: 'Desc' })
// → POST http://localhost:8000/api/items  con body JSON
```

**Por qué centralizar Axios aquí:**
- Si el backend cambia de URL, solo cambias `baseURL` en un lugar
- Aquí también se puede agregar un token de autenticación para todas las peticiones
- El manejo de errores global se configura una sola vez

---

### 7. FastAPI — El portero del servidor

```python
# backend/main.py

# Permite que el frontend (localhost:5173) hable con el backend (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # solo este origen puede hacer peticiones
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta GET simple — no toca la DB
@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI!", "version": "1.0"}

# Ruta GET — trae todos los items de la DB
@app.get("/api/items", response_model=list[ItemResponse])
def get_items(db: Session = Depends(get_db)):
    return db.query(Item).all()

# Ruta POST — crea un item nuevo en la DB
@app.post("/api/items", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)  # recarga el objeto con el id generado por la DB
    return db_item
```

**Qué hace cada parte:**
- `CORSMiddleware` — sin esto, el navegador bloquearía las peticiones del frontend al backend (política de seguridad del navegador)
- `@app.get(...)` / `@app.post(...)` — decoradores que le dicen a FastAPI en qué URL escuchar y con qué método HTTP
- `response_model` — le dice a Pydantic cómo serializar la respuesta antes de enviarla
- `Depends(get_db)` — FastAPI automáticamente abre una sesión de DB al inicio y la cierra al terminar

---

### 8. Pydantic — El validador

Pydantic actúa en dos momentos: al recibir datos (entrada) y al enviar datos (salida).

```python
# backend/schemas.py

# Al RECIBIR (POST /api/items): FastAPI usa esto para validar el body
class ItemCreate(BaseModel):
    name: str          # obligatorio — si falta, FastAPI devuelve error 422 automáticamente
    description: str   # obligatorio

# Al ENVIAR (GET /api/items): controla exactamente qué campos se exponen
class ItemResponse(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True  # permite convertir objetos SQLAlchemy a este schema
```

**Por qué es importante:**
- `ItemCreate` no tiene `id` — el frontend no puede mandar el id, lo genera la DB
- `ItemResponse` sí tiene `id` — el frontend lo recibe para poder identificar cada item
- Si el modelo tuviera un campo `password`, simplemente no lo incluyes en `ItemResponse` y nunca se expone

---

### 9. SQLAlchemy — El traductor

```python
# backend/database.py — la conexión
engine = create_engine("sqlite:///./hello.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()  # clase base para todos los modelos
```

```python
# backend/models.py — define la estructura de la tabla
class Item(Base):
    __tablename__ = "items"               # nombre de la tabla en SQLite

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
```

```python
# backend/main.py — SQLAlchemy en acción
Base.metadata.create_all(bind=engine)   # crea las tablas si no existen (al arrancar)

# Equivale a: SELECT * FROM items;
db.query(Item).all()

# Equivale a: INSERT INTO items (name, description) VALUES (?, ?);
db_item = Item(name=item.name, description=item.description)
db.add(db_item)
db.commit()
```

**Lo que hace `get_db()`:**

```python
def get_db():
    db = SessionLocal()   # abre la conexión
    try:
        yield db          # la presta a la función que la necesita
    finally:
        db.close()        # la cierra siempre, aunque haya un error
```

---

### 10. SQLite — El archivo que guarda todo

SQLite es el destino final de los datos. Es el archivo `hello.db` que aparece en tu carpeta `backend/` cuando corres el servidor por primera vez. No necesita instalación — Python incluye soporte nativo para SQLite.

```python
# backend/database.py
DATABASE_URL = "sqlite:///./hello.db"
#              ↑ protocolo  ↑ ruta relativa al archivo
```

**En desarrollo:** SQLite es perfecto porque es un solo archivo, sin configuración.
**En producción:** cambiar a PostgreSQL es tan simple como cambiar esta línea:
```python
DATABASE_URL = "postgresql://usuario:password@localhost/mi_db"
```
El resto del código (modelos, rutas, schemas) no cambia.

---

## 6. El código completo

### Backend

#### `backend/database.py`

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./hello.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### `backend/models.py`

```python
from sqlalchemy import Column, Integer, String
from database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
```

#### `backend/schemas.py`

```python
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str
    description: str

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True
```

#### `backend/main.py`

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, get_db, Base
from models import Item
from schemas import ItemCreate, ItemResponse

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI!", "version": "1.0"}

@app.get("/api/items", response_model=list[ItemResponse])
def get_items(db: Session = Depends(get_db)):
    return db.query(Item).all()

@app.post("/api/items", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
```

---

### Frontend

#### `frontend/src/main.ts`

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
```

#### `frontend/src/api/axios.ts`

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export default api
```

#### `frontend/src/router/index.ts`

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ItemsView from '../views/ItemsView.vue'

const routes = [
  { path: '/',       name: 'Home',  component: HomeView  },
  { path: '/items',  name: 'Items', component: ItemsView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
```

#### `frontend/src/stores/helloStore.ts`

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/axios'

interface HelloResponse {
  message: string
  version: string
}

export const useHelloStore = defineStore('hello', () => {
  const data = ref<HelloResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchHello() {
    loading.value = true
    error.value = null
    try {
      const res = await api.get<HelloResponse>('/hello')
      data.value = res.data
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, fetchHello }
})
```

#### `frontend/src/stores/itemsStore.ts`

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/axios'

interface Item {
  id: number
  name: string
  description: string
}

interface ItemCreate {
  name: string
  description: string
}

export const useItemsStore = defineStore('items', () => {
  const items = ref<Item[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchItems() {
    loading.value = true
    error.value = null
    try {
      const res = await api.get<Item[]>('/items')
      items.value = res.data
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function createItem(payload: ItemCreate) {
    loading.value = true
    error.value = null
    try {
      const res = await api.post<Item>('/items', payload)
      items.value.push(res.data)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return { items, loading, error, fetchItems, createItem }
})
```

#### `frontend/src/App.vue`

```vue
<script setup lang="ts">
</script>

<template>
  <nav>
    <RouterLink to="/">Home</RouterLink> |
    <RouterLink to="/items">Items</RouterLink>
  </nav>

  <main>
    <RouterView />
  </main>
</template>
```

#### `frontend/src/views/HomeView.vue`

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useHelloStore } from '../stores/helloStore'

const store = useHelloStore()

onMounted(() => store.fetchHello())
</script>

<template>
  <div>
    <h1>🏠 Home</h1>
    <p v-if="store.loading">Cargando...</p>
    <p v-else-if="store.error" style="color:red">❌ {{ store.error }}</p>
    <div v-else-if="store.data">
      <p>{{ store.data.message }}</p>
      <p>Versión: {{ store.data.version }}</p>
    </div>
  </div>
</template>
```

#### `frontend/src/views/ItemsView.vue`

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useItemsStore } from '../stores/itemsStore'

const store = useItemsStore()
const newName = ref('')
const newDescription = ref('')

onMounted(() => store.fetchItems())

async function handleSubmit() {
  if (!newName.value.trim()) return
  await store.createItem({
    name: newName.value,
    description: newDescription.value,
  })
  newName.value = ''
  newDescription.value = ''
}
</script>

<template>
  <div>
    <h1>📦 Items</h1>

    <form @submit.prevent="handleSubmit">
      <input v-model="newName" placeholder="Nombre" required />
      <input v-model="newDescription" placeholder="Descripción" />
      <button type="submit" :disabled="store.loading">Agregar</button>
    </form>

    <p v-if="store.loading">Cargando...</p>
    <p v-else-if="store.error" style="color:red">❌ {{ store.error }}</p>
    <ul v-else>
      <li v-for="item in store.items" :key="item.id">
        <strong>{{ item.name }}</strong> — {{ item.description }}
      </li>
    </ul>
  </div>
</template>
```

---

## 7. Troubleshooting

### `ModuleNotFoundError: No module named 'database'`

Python no encuentra los módulos locales. Agrega al inicio de `main.py`:

```python
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
```

### `Error loading ASGI app. Attribute "app" not found`

Asegúrate de correr uvicorn **desde dentro** de la carpeta `backend/`:

```bash
cd mi-proyecto/backend
uvicorn main:app --reload
```

### `ImportError: cannot import name 'declarative_base' from 'sqlalchemy.ext.declarative'`

SQLAlchemy 2.0 cambió la ubicación. Usa:

```python
from sqlalchemy.orm import sessionmaker, declarative_base  # ✅
# en vez de:
from sqlalchemy.ext.declarative import declarative_base   # ❌
```

### El frontend no puede conectar con el backend (CORS error)

Verifica que el backend tenga `CORSMiddleware` con el origen correcto:

```python
allow_origins=["http://localhost:5173"]
```

Y que ambos servidores estén corriendo al mismo tiempo.

### `npm create vite` no reconoce el template

Asegúrate de tener Node.js 18+:

```bash
node --version   # debe ser v18 o superior
```

---

*Generado como guía de referencia para el proyecto Full Stack Hello World*