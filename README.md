
---

# Web-Based Dynamic Pathfinding Agent (Wumpus World)

## Project Overview

This project implements a **Knowledge-Based Agent** that navigates a Wumpus World-style grid using **Propositional Logic and Resolution Refutation**.
The agent dynamically perceives its environment and uses logical inference to safely explore the grid while avoiding hazards.

---

## Objective

* Build an intelligent agent capable of reasoning under uncertainty
* Use Propositional Logic (Knowledge Base + Inference) for decision-making
* Implement Resolution Refutation to prove safe cells
* Provide a web-based visualization of the agent’s behavior

---

## Environment Features

* Dynamic Grid Size (User-defined Rows × Columns)
* Random Hazard Placement (Pits and Wumpus)
* Percepts System

  * Breeze → Adjacent Pit
  * Stench → Adjacent Wumpus

---

## Inference Engine

### Knowledge Base (KB)

The agent stores logical rules such as:

```
B_2,1 ⇔ (P_2,2 ∨ P_3,1 ∨ P_1,1)
```

---

### ASK (Resolution Refutation)

Before moving, the agent checks:

```
¬P(i,j) ∧ ¬W(i,j)
```

Steps:

1. Convert KB to CNF
2. Add negated query
3. Apply Resolution
4. If contradiction (⊥) is found, the cell is safe

---

## Visualization

### Grid Representation

* Green → Safe Cells
* Gray → Unknown Cells
* Red → Hazards

### Dashboard

* Inference Steps Counter
* Current Percepts (Breeze/Stench)
* Agent Position

---

## Technologies Used

* Frontend: HTML, CSS, JavaScript / React
* Logic Engine: JavaScript (CNF Conversion and Resolution Algorithm)
* Deployment: Pythonanywhere

---

## How to Run the Project

### 1. Clone Repository

```
git clone https://github.com/your-username/wumpus-agent.git
cd wumpus-agent
```

### 2. Install Dependencies (if using React)

```
npm install
```

### 3. Run Locally

```
npm start
```

---

## Live Demo

https://MaryamZahidAI.pythonanywhere.com


---

## Screenshots

Include screenshots of:

* Initial Grid
* Agent Movement
* Inference Process
* Dashboard Metrics

---

## System Workflow

1. Initialize grid and hazards
2. Agent starts at initial position
3. Receive percepts
4. Update KB (TELL)
5. Query KB (ASK using Resolution)
6. Move to a safe cell
7. Repeat until goal is reached or no safe moves remain

---

## Challenges

* Efficient implementation of Resolution
* Managing large clause sets
* Maintaining real-time UI responsiveness

---

## Future Improvements

* Extend to First-Order Logic
* Optimize inference using heuristics
* Introduce multi-agent scenarios
* Add learning-based enhancements

---

## Author

Maryam Zahid
FAST-NUCES (Chiniot-Faisalabad Campus)

---

## License

This project is for academic purposes only.

---

