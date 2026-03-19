Title: xxx
Course: Any Course
Student: Me
Professor: Mr. Professor Aros-Vera
Institution: Please accept me
Date: Today

---

# Modelo Avanzado: Facility Location Estocastico con Expansion de Capacidad

## Que quise agregar en esta version

En el ejemplo basico, la idea de Benders ya se entiende bien, pero el modelo sigue siendo bastante limpio: una sola demanda, una sola estructura de capacidad y una sola variable `theta`. En esta version quise meterle un poco mas de realismo sin llegar todavia al nivel de maestria o PhD.

Por eso este modelo agrega tres cosas importantes:

- demanda por escenarios,
- expansion modular de capacidad,
- Benders multicorte.

La gracia de este salto es que el problema ya no busca una red buena para un solo caso, sino una red que siga funcionando bien cuando la demanda cambia.

## Como esta dividido el modelo

### Master problem

El master se queda con las decisiones estrategicas:

- `y[i]`: si abro o no la instalacion `i`,
- `z[i]`: cuantos modulos extra instalo en `i`,
- `theta[s]`: una aproximacion del costo operativo en cada escenario.

La funcion objetivo combina:

- costo fijo de apertura,
- costo de expansion,
- costo esperado de distribucion.

### Subproblem por escenario

Una vez fijadas `y` y `z`, cada escenario resuelve su propio problema de transporte. En otras palabras, para cada nivel de demanda el subproblema decide cuanto enviar desde cada instalacion a cada cliente minimizando el costo de distribucion.

## Por que esta version ya es bastante mas interesante

### 1. La demanda deja de ser unica

Ahora no hay una sola demanda "correcta". En vez de eso, hay escenarios `Low`, `Base` y `High`, cada uno con una probabilidad. Eso obliga al master a tomar decisiones que no sean buenas solo para un caso.

### 2. La capacidad tambien se puede invertir

No solo se decide abrir o no abrir una instalacion. Tambien se puede expandir capacidad mediante modulos. Eso hace que el master tenga mas flexibilidad, pero tambien mas combinaciones posibles.

### 3. Multi-cut Benders transmite mejor la informacion

En lugar de usar una sola variable `theta`, uso una `theta[s]` por escenario. Lo hice asi porque cada escenario entrega informacion distinta sobre el costo operativo, y conviene que el master la reciba por separado.

## Tipo de cortes

### Feasibility cut

En esta instancia, cualquier instalacion puede atender a cualquier cliente. Entonces, si la capacidad instalada total no alcanza la demanda total de un escenario, el subproblema queda infactible. El corte de factibilidad refleja justamente esa idea:

```text
sum_i (base_i y_i + mod_i z_i) >= demanda_total_escenario
```

### Optimality cut

Cuando el subproblema es factible, sus duales generan un corte de optimalidad por escenario:

```text
theta_s >= constante_dual + terminos_en_y + terminos_en_z
```

Ese corte obliga al master a reconocer mejor el costo real de operar la red que acaba de elegir.

## Resultado validado en esta instancia

La ejecucion que ya deje validada produjo lo siguiente:

- instalaciones abiertas: `F2`, `F3`, `F5`,
- modulos instalados: `1` modulo en `F2`,
- costo fijo de apertura: `500`,
- costo de expansion: `52`,
- costo esperado de transporte: `815.40`,
- costo total esperado: `1367.40`,
- `1` feasibility cut,
- `30` optimality cuts,
- convergencia con `LB = UB = 1367.40`.

Los costos de transporte por escenario fueron:

- `Low = 605`,
- `Base = 790`,
- `High = 998`.

## Como lo interpretaria

Para mi, este es el punto donde el ejemplo deja de ser solo didactico y empieza a parecerse a una decision de diseno de red bajo incertidumbre. El modelo ya esta balanceando apertura, expansion y operacion esperada. Ademas, como hay escenarios, la solucion final no responde solo a un costo puntual, sino a una logica de desempeno esperado.

## Archivo a ejecutar

- [advanced_stochastic_benders_facility_location.py](C:\Users\Ferna\Desktop\Facility Location and Distribution\02_advanced\advanced_stochastic_benders_facility_location.py)

## Como correrlo

```powershell
py "C:\Users\Ferna\Desktop\Facility Location and Distribution\02_advanced\advanced_stochastic_benders_facility_location.py"
```
