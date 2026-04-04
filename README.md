# 🧠 Se'si Eskani

Plataforma web para dar cumplimiento y gestionar la información relacionada a los atributos de egreso del plan educativo de Ingeniería Industrial del Instituto Tecnológico Superior de Huetamo.

---

## ⚙️ Tecnologías

- **Backend:** Django
- **Frontend:** HTML, SASS
- **Base de datos:** PostgreSQL
- **Infraestructura:** Docker, Nginx
- **Herramientas frontend:** Node.js y npm para la compilación de SASS

---

## 🚀 Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd CACEI
```

### 2. Configurar variables de entorno

Crear un archivo `.env` basado en el archivo de ejemplo:

```bash
cp .env.example .env
```

Editar las variables según sea necesario.

### 3. Instalar dependencias de Node.js

Estas dependencias se utilizan para compilar los estilos SASS del proyecto.

```bash
npm install
```

### 4. Levantar el proyecto con Docker

```bash
docker compose up --build
```

### 5. Aplicar migraciones

En otra terminal:

```bash
docker compose exec web python manage.py migrate
```

### 6. Acceder al sistema

Abrir en el navegador:

```text
http://localhost
```

---

## 📂 Estructura del proyecto

```text
CACEI/
│
├── CACEI/               # Configuración principal del proyecto Django
├── core/                # Aplicación principal Django
├── media/               # Archivos subidos
├── nginx/               # Configuración de Nginx
├── node_modules/        # Dependencias de Node.js
├── staticfiles/         # Archivos estáticos compilados
│
├── .dockerignore
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yaml
├── dockerfile
├── manage.py
├── package-lock.json
├── package.json         # Dependencias y scripts de Node.js
├── README.md
├── requirements.txt
```

---

## 🎨 Compilación de estilos SASS

El proyecto utiliza SASS mediante dependencias de Node.js.

Instalar dependencias:

```bash
npm install
```

Compilar estilos según los scripts definidos en `package.json`:

```bash
npm run build
```

Si el proyecto cuenta con un script de vigilancia para desarrollo, puede ejecutarse con:

```bash
npm run sass
```

> Revisa los scripts disponibles en el archivo `package.json`.

---

## 🔐 Variables de entorno

Las variables necesarias se encuentran documentadas en:

```text
.env.example
```

Algunas variables comunes incluyen:

- `SECRET_KEY`
- `DEBUG`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

---

## 🧪 Comandos útiles

### Crear superusuario

```bash
docker compose exec web python manage.py createsuperuser
```

### Recolectar archivos estáticos

```bash
docker compose exec web python manage.py collectstatic --noinput
```

### Instalar dependencias frontend

```bash
npm install
```

---

## 📌 Notas

- Asegúrate de tener Docker y Docker Compose instalados.
- Asegúrate también de tener Node.js y npm instalados si vas a compilar o modificar los estilos SASS.
- El proyecto utiliza Nginx como proxy reverso.
- Las configuraciones pueden variar dependiendo del entorno.
