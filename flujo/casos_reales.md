# Casos reales de WhatsApp - KitraDep

> Estos son 2 chats reales (con datos personales censurados) que muestran
> los dos flujos maestros del negocio: **ISAPRE/Particular** y **FONASA**.
> Los usamos como fuente de verdad para el diseno del bot.

---

## CASO 1 - ISAPRE (Javiera, 3/6/2026)

**Patron detectado:**
1. Saludo del paciente.
2. Bot/humano saluda y pregunta motivo.
3. Paciente dice "quiero kinesiologia + saber valores".
4. **Pregunta clave:** "cuentenos si ya dispone de una orden o derivacion medica a kinesiologia".
5. Paciente confirma que tiene orden -> le pide que la envie por foto.
6. **Explicacion obligatoria:** "nuestras atenciones son personalizadas, cada kine trabaja con un solo paciente por sesion".
7. **Pregunta bifurcacion:** "tenemos valores preferenciales para fonasa, y valores isapre. Cual es tu prevision?"
8. Paciente: "Isapre".
9. **Muestra valores ISAPRE:**
   - 1 sesion: $25.000
   - 5 sesiones: $115.000
   - 10 sesiones: $230.000
10. Paciente pregunta por reembolso.
11. Confirma: **"Dan las boletas para realizar el reembolso, exactamente!"**
12. Pregunta horario de preferencia (AM / PM).
13. **Ofrece 2 slots concretos**: "para maniana 11:45 y viernes 12:30 hrs".
14. Paciente elige dia.
15. Pide **datos completos**: Nombre, RUT, Correo, Contacto, Prevision, Direccion.
16. Pregunta modalidad de pago: **sesion a sesion ($25.000) vs pack 10 ($230.000 pago completo)**.
17. Aclara: **"puede pagar en la consulta, se lo firmamos a la profesional"**.
18. Confirma cita: "te esperamos el viernes a las 12:30 hrs, la kinesiologa Javiera Caceres te atendera".
19. Envia **ubicacion Google Maps**: Llano Subercaseaux 3791, San Miguel.
20. Info extra (bicicletero -> consultar conserje, llevar candado).

---

## CASO 2 - FONASA (Roxana, 19/3/2026 - 30/3/2026)

**Patron detectado:**
1. Saludo del paciente.
2. **Bot responde con auto-mensaje:** "Gracias por comunicarte con KitraDep. Nos puedes contar brevemente el motivo? Si tienes orden medica, puedes enviarla por aqui. Pronto uno de nuestros kinesiologos respondera".
3. Paciente confirma orden -> envia foto.
4. Pregunta contextual: "realizas un deporte en particular?" (por reintegro deportivo).
5. **Explicacion obligatoria:** "atenciones solo personalizadas, cada kine atiende a un solo paciente. Sesiones duran 45-50 min. En primera sesion hacemos evaluacion inicial e historia".
6. Pregunta: "te interesaria agendar una sesion de evaluacion".
7. **Bifurcacion FONASA** (paciente pregunta "aceptan Fonasa?"):
   - Aclara: **"No trabajamos con bonos propiamente tal, ya que nuestras atenciones son 1 a 1"**.
   - Pero tienen **valor preferencial**.
   - **Valores FONASA:**
     - 1 sesion: $20.000 (valor general $25.000)
     - Pack 5: $100.000 (valor general $115.000)
     - Pack 10: $180.000 (valor general $230.000)
   - Aclaracion: "aunque no somos centro adherido a FONASA, si entregamos valor preferencial. Este es un apoyo que entregamos como consulta para que puedas acceder a rehabilitacion de calidad y personalizada".
8. **Auto-mensaje fuera de horario:** "En estos momentos no nos encontramos disponibles, responderemos a la brevedad. Horarios: L-V 8-21h, Sab 9-13h. Si necesitas info y agendar: https://kinetraumadeportivo.com/kinesiologia-en-san-miguel/".
9. Ofrece **link autogestion**: https://encuadrado.com/centro/kitradep
10. Info kines por franja horaria:
    - **AM**: Javiera y Jaime
    - **PM**: Francisco y Valentina
11. Pregunta horario de preferencia.
12. Ofrece slot concreto: "a las 11:45 le podemos ofrecer para mnn".
13. Pide **datos completos** (misma plantilla que caso 1).
14. Confirma cita.
15. Tip: **"asistir con ropa comoda, te puedes cambiar alla mismo si lo necesitas"**.

---

## Reglas maestras que se destilan

| Regla | Detalle |
|---|---|
| **Servicio unico** | Es kinesiologia 1-a-1 (45-50 min). Lo que cambia es la PREVISION, no el servicio. |
| **Primera sesion** | Siempre incluye evaluacion inicial + historia del paciente. |
| **Orden medica** | Se pregunta si la tiene, si si -> pedir foto. NO es obligatoria. |
| **Bifurcacion Fonasa vs Isapre** | Antes de mostrar valores, SIEMPRE preguntar prevision. |
| **Fonasa - aclaracion legal** | "No somos centro adherido a Fonasa, damos valor preferencial". OBLIGATORIO decirlo. |
| **Isapre - reembolso** | Si preguntan: "damos boletas para reembolso". |
| **Modalidad pago** | Se puede pagar sesion a sesion o pack completo. Pago presencial en consulta. |
| **Kines por franja** | AM: Javiera Caceres, Jaime. PM: Francisco, Valentina. |
| **Datos requeridos** | Nombre, RUT, Correo, Contacto, Prevision, Direccion. |
| **Post-cita: dar** | Confirmacion + kine asignado + ubicacion Maps + tip (ropa comoda / bicicletero). |
| **Bot no cierra agenda solo** | En Fase 1, recolecta info y "un kine confirma horario" o deriva al link de autogestion. |

---

## Data del negocio (fuente de verdad)

- **Nombre**: KitraDep (Kine Trauma Deportivo)
- **Direccion**: Llano Subercaseaux 3791, oficina 208-209 (2do piso), San Miguel, Region Metropolitana
- **Como llegar**: salida poniente de metro San Miguel
- **Maps**: https://maps.app.goo.gl/U7ByTKYjp2sDqNTq7?g_st=ic
- **Web**: https://kinetraumadeportivo.com/kinesiologia-en-san-miguel/
- **Agenda online**: https://encuadrado.com/centro/kitradep
- **Horarios**: Lunes a Viernes 08:00-21:00 hrs / Sabados 09:00-13:00 hrs
- **Bicicletero**: si (consultar conserje, llevar candado)
