# 008 - Acceder a la interfaz web

## Objetivo

Verificar que la interfaz web de Graylog se encuentre disponible y que sea posible autenticarse con el usuario administrador.

## Requisitos

- Graylog iniciado en los tres nodos.
- API REST respondiendo correctamente.
- Puerto TCP 9000 accesible desde el equipo administrador.

## Procedimiento

### 1. Abrir la interfaz web

Desde un navegador acceder a:

Nodo gl01:

```text
http://gl01:9000
```

o

```text
http://192.168.122.101:9000
```

---

### 2. Iniciar sesión

Usuario:

```text
admin
```

Contraseña:

La contraseña utilizada para generar el valor de `root_password_sha2` durante el procedimiento **004-generate-secrets.md**.

---

### 3. Verificar el acceso

Una vez autenticado deberá mostrarse la interfaz principal de Graylog.

Verificar que:

- El acceso se realiza correctamente.
- No aparecen errores de conexión.
- La interfaz responde normalmente.

## Archivos modificados

Ninguno.

## Validación

Comprobar que:

- La página de inicio de sesión es accesible.
- Es posible autenticarse con el usuario `admin`.
- La interfaz principal carga correctamente.

## Resultado esperado

Graylog se encuentra completamente instalado y accesible mediante la interfaz web.

## Checklist

- [ ] Interfaz web accesible.
- [ ] Inicio de sesión exitoso.
- [ ] Interfaz principal visible.

## Próximo paso

La instalación del cluster Graylog ha finalizado.

Las tareas de operación (Inputs, Streams, Dashboards, búsqueda de mensajes, etc.) se documentarán de forma independiente.