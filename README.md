# DevOps Roadmap 2026

Curso abierto en español, generado con **Python** y publicado como sitio estático para **GitHub Pages**.

Temario basado en el [DevOps Roadmap 2026](https://github.com/milanm/DevOps-Roadmap) de Dr. Milan Milanović y Romano Roth. La pedagogía sigue el espíritu de CS50 (Harvard): piso bajo y techo alto, conferencia → cortos → problem set, vías estándar y hacker, rúbrica de correctitud / diseño / estilo, recuerdo activo y repetición espaciada.

## Sitio

**https://lalostatic.github.io/DevOps-Roadmap/**

La primera vez hay que encender Pages (GitHub no lo permite por API con este token):

1. Abre [Settings → Pages](https://github.com/lalostatic/DevOps-Roadmap/settings/pages)
2. **Build and deployment** → Source: **Deploy from a branch**
3. Branch: **main** · carpeta: **/docs**
4. Save. En uno o dos minutos el curso queda en el enlace de arriba.

## Índice

En cualquier página, **Buscar temario** (o la tecla `/`) abre el índice del documento: 12 semanas + bonus, herramientas, libros, glosario y recursos. La página [Índice](https://lalostatic.github.io/DevOps-Roadmap/temario.html) es la tabla de contenidos completa.

## Cómo está hecho

GitHub Pages no ejecuta Python en el navegador. Python **genera** HTML/CSS/JS estáticos:

```bash
python3 course/build.py
```

La salida queda en `docs/`. No hay dependencias: solo Python 3 de la biblioteca estándar.

## Método

El curso se lee como un **libro**: portada, índice, prólogo y capítulos. Dentro de cada capítulo se hojear (flechas, esquina o Siguiente).

1. Elige comodidad (menos / más cómodo).
2. Abre el capítulo y pasa folios: conferencia → cortos → recorrido → problem set → recuerdo → Feynman → tarjetas.
3. Cortos de un concepto.
4. Recorrido para arrancar.
5. Problem set estándar o hacker.
6. Quiz de recuerdo, Feynman y tarjetas Leitner.

El progreso se guarda en `localStorage` de tu navegador.

## Créditos

Roadmap original: TechWorld With Milan. Este repositorio es un curso derivado en español, no un reemplazo del PDF original.
