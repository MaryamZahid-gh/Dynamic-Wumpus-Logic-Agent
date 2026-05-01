import random
from flask import Flask, jsonify, render_template, request, session
import json, uuid

app = Flask(__name__)
app.secret_key = 'wumpus-kb-secret-2025'


class KnowledgeBase:
    def __init__(self):
        self.clauses: set[frozenset] = set()
        self.inference_steps = 0

    @staticmethod
    def negate(lit: str) -> str:
        return lit[1:] if lit.startswith('~') else f'~{lit}'

    def _add(self, clause):
        self.clauses.add(frozenset(clause))

    def tell_fact(self, literal: str):
        self._add([literal])

    def tell_biconditional_breeze(self, r, c, neighbors):
        B = f'B_{r}_{c}'
        pits = [f'P_{nr}_{nc}' for nr, nc in neighbors]
        self._add([f'~{B}'] + pits)
        for pit in pits:
            self._add([f'~{pit}', B])

    def tell_biconditional_stench(self, r, c, neighbors):
        S = f'S_{r}_{c}'
        wumpi = [f'W_{nr}_{nc}' for nr, nc in neighbors]
        self._add([f'~{S}'] + wumpi)
        for w in wumpi:
            self._add([f'~{w}', S])

    def _resolve(self, c1, c2, lit):
        self.inference_steps += 1
        resolvent = (c1 - {lit}) | (c2 - {self.negate(lit)})
        for l in resolvent:
            if self.negate(l) in resolvent:
                return None  # tautology
        return resolvent

    def ask(self, literal: str) -> bool:
        neg = self.negate(literal)
        working = set(self.clauses)
        working.add(frozenset([neg]))
        seen = set(working)
        changed = True
        iterations = 0

        while changed and iterations < 600:
            changed = False
            iterations += 1
            clause_list = list(working)
            new_clauses = []

            for i, c1 in enumerate(clause_list):
                for c2 in clause_list[i + 1:]:
                  
        
                    for lit in list(c1) + list(c2):
                        neg_lit = self.negate(lit)
                        if lit in c1 and neg_lit in c2:
                            resolvent = self._resolve(c1, c2, lit)
                        elif lit in c2 and neg_lit in c1:
                            resolvent = self._resolve(c2, c1, lit)
                        else:
                            continue
                        if resolvent is None:
                            continue
                        if len(resolvent) == 0:
                            self.inference_steps += 1
                            return True 
                        fs = frozenset(resolvent)
                        if fs not in seen:
                            seen.add(fs)
                            new_clauses.append(fs)
                            changed = True
            working.update(new_clauses)

        return False

    def ask_safe(self, r, c):
        return self.ask(f'~P_{r}_{c}') and self.ask(f'~W_{r}_{c}')

    def ask_pit(self, r, c):
        return self.ask(f'P_{r}_{c}')

    def ask_wumpus(self, r, c):
        return self.ask(f'W_{r}_{c}')

    def get_clauses_display(self):
        result = []
        for clause in list(self.clauses)[-40:]:
            result.append('(' + ' ∨ '.join(sorted(clause)) + ')')
        return result


class WumpusWorld:
    def __init__(self, rows=4, cols=4, num_pits=3):
        self.rows = rows
        self.cols = cols
        self.pits: set = set()
        self.wumpus = None
        self.gold = None
        self.agent = (0, 0)
        self.alive = True
        self.gold_found = False
        self.kb = KnowledgeBase()
        self.visited: set = set()
        self.safe_cells: set = set()
        self.confirmed_pits: set = set()
        self.confirmed_wumpus: set = set()
        self.moves = 0
        self.log = []
        self.status = 'running'
        self._place_hazards(num_pits)
        self._bootstrap()

    def _place_hazards(self, num_pits):
        candidates = [(r, c) for r in range(self.rows)
                      for c in range(self.cols) if (r, c) != (0, 0)]
        random.shuffle(candidates)
        count = min(num_pits, len(candidates) - 2)
        for pos in candidates[:count]:
            self.pits.add(pos)
        non_pit = [p for p in candidates if p not in self.pits]
        random.shuffle(non_pit)
        self.wumpus = non_pit[0] if non_pit else (self.rows - 1, self.cols - 1)
        self.gold = non_pit[1] if len(non_pit) > 1 else (self.rows - 1, self.cols - 1)

    def _bootstrap(self):
        self.safe_cells.add((0, 0))
        self.kb.tell_fact('~P_0_0')
        self.kb.tell_fact('~W_0_0')
        self._process_cell(0, 0)

    def neighbors(self, r, c):
        return [(nr, nc) for nr, nc in [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
                if 0 <= nr < self.rows and 0 <= nc < self.cols]

    def percepts(self, r, c):
        p = []
        nbrs = self.neighbors(r, c)
        if any(n in self.pits for n in nbrs): p.append('BREEZE')
        if any(n == self.wumpus for n in nbrs): p.append('STENCH')
        if (r, c) == self.gold: p.append('GLITTER')
        return p

    def _process_cell(self, r, c):
        self.visited.add((r, c))
        perc = self.percepts(r, c)
        nbrs = self.neighbors(r, c)

        if 'BREEZE' in perc:
            self.kb.tell_fact(f'B_{r}_{c}')
            self.kb.tell_biconditional_breeze(r, c, nbrs)
            self._log(f'TELL: B_{r}_{c} → breeze at ({r},{c})', 'tell')
            self._log('TELL: B_{r}_{c} ⟺ '.format(r=r, c=c) +
                      ' ∨ '.join(f'P_{nr}_{nc}' for nr, nc in nbrs), 'tell')
        else:
            self.kb.tell_fact(f'~B_{r}_{c}')
            for nr, nc in nbrs:
                self.kb.tell_fact(f'~P_{nr}_{nc}')
                self.safe_cells.add((nr, nc))
            self._log(f'TELL: ¬B_{r}_{c} → no pits adjacent to ({r},{c})', 'tell')

        if 'STENCH' in perc:
            self.kb.tell_fact(f'S_{r}_{c}')
            self.kb.tell_biconditional_stench(r, c, nbrs)
            self._log(f'TELL: S_{r}_{c} → stench at ({r},{c})', 'tell')
        else:
            self.kb.tell_fact(f'~S_{r}_{c}')
            for nr, nc in nbrs:
                self.kb.tell_fact(f'~W_{nr}_{nc}')
            self._log(f'TELL: ¬S_{r}_{c} → no wumpus adjacent to ({r},{c})', 'tell')

        for nr, nc in nbrs:
            if (nr, nc) not in self.visited and (nr, nc) not in self.safe_cells:
                self._log(f'ASK: Safe({nr},{nc})? Running resolution refutation...', 'ask')
                if self.kb.ask_safe(nr, nc):
                    self.safe_cells.add((nr, nc))
                    self._log(f'PROVEN: ({nr},{nc}) is SAFE ✓', 'infer')
            if (nr, nc) not in self.confirmed_pits:
                if self.kb.ask_pit(nr, nc):
                    self.confirmed_pits.add((nr, nc))
                    self._log(f'PROVEN: ({nr},{nc}) contains a PIT ⚠', 'warn')
            if (nr, nc) not in self.confirmed_wumpus:
                if self.kb.ask_wumpus(nr, nc):
                    self.confirmed_wumpus.add((nr, nc))
                    self._log(f'PROVEN: ({nr},{nc}) contains WUMPUS ⚠', 'warn')

    def _log(self, msg, kind='entry'):
        self.log.append({'msg': msg, 'kind': kind})
        if len(self.log) > 200:
            self.log.pop(0)

    def best_move(self):
        r, c = self.agent
        nbrs = self.neighbors(r, c)
  
        hazard = self.confirmed_pits | self.confirmed_wumpus

        safe_unvisited = [(nr, nc) for nr, nc in nbrs
                          if (nr, nc) not in self.visited and (nr, nc) in self.safe_cells]
        if safe_unvisited:
            return safe_unvisited[0]

     
        safe_visited = [(nr, nc) for nr, nc in nbrs
                        if (nr, nc) in self.visited
                        and (nr, nc) not in hazard
                        and (nr, nc) != (r, c)]
        if safe_visited:
            return safe_visited[0]


        unknown = [(nr, nc) for nr, nc in nbrs if (nr, nc) not in hazard]
        if unknown:
            return unknown[0]

        return None

    def step(self):
        if not self.alive or self.status != 'running':
            return self.status

        move = self.best_move()
        if move is None:
            self.status = 'stuck'
            return 'stuck'

        r, c = move
        self.agent = (r, c)
        self.moves += 1

        if (r, c) in self.pits:
            self.alive = False
            self.status = 'pit'
            self._log(f'AGENT fell into PIT at ({r},{c})! 💀', 'warn')
            return 'pit'

        if (r, c) == self.wumpus:
            self.alive = False
            self.status = 'wumpus'
            self._log(f'AGENT eaten by WUMPUS at ({r},{c})! 💀', 'warn')
            return 'wumpus'

        self._process_cell(r, c)

        if 'GLITTER' in self.percepts(r, c):
            self.gold_found = True
            self.status = 'gold'
            self._log(f'GOLD RETRIEVED at ({r},{c})! 🏆', 'infer')
            return 'gold'

        return 'ok'

    def to_dict(self, reveal=False):
        cells = []
        for r in range(self.rows):
            for c in range(self.cols):
                pos = (r, c)
                ar, ac = self.agent
                perc = self.percepts(r, c) if pos in self.visited else []
                cell = {
                    'r': r, 'c': c,
                    'is_agent': pos == (ar, ac),
                    'visited': pos in self.visited,
                    'safe': pos in self.safe_cells,
                    'confirmed_pit': pos in self.confirmed_pits,
                    'confirmed_wumpus': pos in self.confirmed_wumpus,
                    'percepts': perc,
                    'has_pit': pos in self.pits if reveal else False,
                    'has_wumpus': pos == self.wumpus if reveal else False,
                    'has_gold': pos == self.gold if (reveal or pos == self.agent) else False,
                }
                cells.append(cell)

        return {
            'rows': self.rows,
            'cols': self.cols,
            'cells': cells,
            'agent': list(self.agent),
            'alive': self.alive,
            'gold_found': self.gold_found,
            'status': self.status,
            'moves': self.moves,
            'inference_steps': self.kb.inference_steps,
            'kb_clauses': len(self.kb.clauses),
            'safe_count': len(self.safe_cells),
            'current_percepts': self.percepts(*self.agent),
            'log': self.log[-50:],
            'cnf_clauses': self.kb.get_clauses_display()[-30:],
        }


worlds = {}


def get_world(sid):
    return worlds.get(sid)


@app.route('/')
def index():
    if 'sid' not in session:
        session['sid'] = str(uuid.uuid4())
    return render_template('index.html')


@app.route('/api/new', methods=['POST'])
def new_game():
    sid = session.get('sid', str(uuid.uuid4()))
    session['sid'] = sid
    data = request.get_json(force=True)
    rows = max(3, min(8, int(data.get('rows', 4))))
    cols = max(3, min(8, int(data.get('cols', 4))))
    pits = max(1, min(12, int(data.get('pits', 3))))
    worlds[sid] = WumpusWorld(rows, cols, pits)
    return jsonify(worlds[sid].to_dict())


@app.route('/api/step', methods=['POST'])
def step():
    sid = session.get('sid')
    w = get_world(sid)
    if not w:
        return jsonify({'error': 'No active game'}), 400
 
    w.step()
    reveal = w.status in ('pit', 'wumpus', 'gold', 'stuck')
    return jsonify(w.to_dict(reveal=reveal))


@app.route('/api/state', methods=['GET'])
def state():
    sid = session.get('sid')
    w = get_world(sid)
    if not w:
        return jsonify({'error': 'No active game'}), 404
    reveal = w.status in ('pit', 'wumpus', 'gold', 'stuck')
    return jsonify(w.to_dict(reveal=reveal))


if __name__ == '__main__':
    import os
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))