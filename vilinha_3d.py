import random 
# =========================================================
# CONFIGURAÇÕES GLOBAIS
# =========================================================
# Variáveis que controlam a câmera e o mundo
giro_camera = 0.12       # Ângulo de rotação horizontal (eixo Y) inicial da maquete
ESCALA = 1.45            # Fator de zoom da maquete. 
CAM_ANGULO = -0.50       # Inclinação da câmera para baixo (visão isométrica/aérea)
tempo_dia = 0.2          # Controla o ciclo dia/noite (0 a 1). 0.2 = Manhã.
CHAO_Y = 40              # Posição base do chão no eixo Y. 

# Variáveis reservadas para as texturas procedurais 
tex_grama = None; tex_parede = None; tex_madeira = None
tex_terra = None; tex_telhados = []

# Variáveis do personagem (Coelhinho)
coelho_x, coelho_z = 0.0, 80.0 # Posição inicial do coelho no mundo 3D
coelho_dir = 0.0               # Ângulo para onde o coelho está olhando
coelho_anda = False            # Estado (booleano) se ele está em movimento ou parado
COELHO_R = 8                   # Raio de colisão do coelho (tamanho da "caixa" invisível ao redor dele)
COELHO_V = 1.8                 # Velocidade de movimento (pixels por frame)

m_drag = False                 # Controle de clique/arraste do mouse (evita conflitos)

# Listas que guardarão os objetos dinâmicos do jogo
fumaca = []; peixes = []; abelhas = []
obstaculos = []; chamine_pos = []; pedras_rio = []

# =========================================================
# DICIONÁRIOS DE LAYOUT (Estruturas de Dados)
# =========================================================
# "x" e "z": Coordenadas no plano horizontal. 
# "cor": Tupla RGB (Red, Green, Blue). "e": Escala da casa. "sh": Cor da janela/persiana. "ch": Tem chaminé. "smoke": Tipo de fumaça
casas = [
    {"x":-80,"z":-40,"cor":(245,110,85), "e":0.60,"r":0,      "ch":True, "sh":(110,148,118), "smoke":"soft"},
    {"x": 30,"z":-43,"cor":(175,110,245),"e":0.64,"r":0,      "ch":True, "sh":(152,128,178), "smoke":"normal"},
    {"x":115,"z": 45,"cor":(110,220,130),"e":0.56,"r":-1.5708,"ch":True, "sh":(122,162,132), "smoke":"soft"}, 
    {"x":-75,"z": 80,"cor":(245,175,70), "e":0.58,"r":0,      "ch":True, "sh":(188,148,108), "smoke":"normal"}, 
]

ruas = [
    {"cx":-15,"cz":7,"w":220,"d":28}, # "w" = largura (width), "d" = profundidade (depth)
    {"cx":75, "cz":60,"w":28, "d":105},
]

postes = [
    {"x":-38,"z":7}, 
    {"x":52, "z":7},
    {"x":60, "z":105}, 
]

arvores = [
    {"x":-135,"z":40, "h":38}, {"x":-128,"z":110,"h":32}, # "h" = altura da árvore
    {"x":35,  "z":120,"h":36}, {"x":142, "z":-23,"h":28},
    {"x":132, "z":105, "h":34}, {"x":-32, "z":130,"h":32},
]

flores = [
    {"x":-130,"z":40}, {"x":-30,"z":100}, {"x":20,"z":67},
    {"x":-38,"z":47}, {"x":100, "z":115}, {"x":-122,"z":100},
]

arbs = [
    {"x":-128,"z":-23,"s":12}, {"x":65,"z":-20,"s":10}, # "s" = tamanho/escala do arbusto
    {"x":145, "z":35, "s":13}, {"x":-120,"z":120,"s":11},
]

RIO_Z = -115 # Posição base do rio no fundo do cenário
RIO_W = 38   # Largura do rio

# =========================================================
# CLASSES BÁSICAS (Orientação a Objetos)
# =========================================================
class Particula:
    """Representa a fumaça saindo das chaminés."""
    def __init__(self, x, y, z, tipo="normal"):
        # Adiciona um leve desvio aleatório para a fumaça não sair em linha reta
        self.x = x + random.uniform(-2, 2)
        self.y = y
        self.z = z + random.uniform(-2, 2)
        self.vy = random.uniform(0.3, 0.6)        # Velocidade de subida (eixo Y)
        self.vx = random.uniform(-0.08, 0.08)     # Vento lateral (eixo X)
        self.vz = random.uniform(-0.08, 0.08)     # Vento de profundidade (eixo Z)
        self.vida = 1.0                           # Vida vai de 1.0 a 0.0 (controla a opacidade)
        self.dec = random.uniform(0.01, 0.018)    # Taxa de decaimento da vida por frame
        self.tam = random.uniform(3, 5)           # Tamanho da bolinha de fumaça
        self.tipo = tipo                          # "normal" ou "soft" (define quão escura ela é)

class Peixe:
    """Máquina de estado que controla os pulos dos peixes."""
    def __init__(self):
        self.x = random.uniform(-160, 160)
        self.z = RIO_Z + random.uniform(-8, 8)
        self.y = CHAO_Y - 2
        self.vy = 0
        self.fase = 0 # 0 = escondido debaixo d'água, 1 = pulando no ar
        self.timer = random.randint(180, 500) # Tempo de espera até o próximo pulo
        self.tam = random.uniform(4, 6)
        self.cor = random.choice([(255,100,0), (255,120,10), (255,140,0)])
        self.rot = 0
        self.splash = [] # Guarda as gotinhas de água geradas ao cair

    def update(self):
        if self.fase == 0:
            self.timer -= 1
            if self.timer <= 0:
                self.fase = 1 # Inicia o pulo
                self.vy = -random.uniform(1.5, 2.5) # Dá um impulso para cima (negativo no Y)
                self.x = random.uniform(-160, 160)  # Sorteia nova posição
                self.z = RIO_Z + random.uniform(-8, 8)
        else:
            self.vy += 0.08 # Gravidade puxando o peixe de volta
            self.y += self.vy
            self.rot += 0.05 # Gira o corpo do peixe
            # Se bateu na água (CHAO_Y - 2)...
            if self.y >= CHAO_Y - 2 and self.vy > 0:
                self.fase = 0
                self.timer = random.randint(250, 600)
                self.y = CHAO_Y - 2
                self.rot = 0
                # Gera 3 gotinhas de splash
                for _ in range(3):
                    self.splash.append([
                        self.x+random.uniform(-3,3), float(self.y),
                        self.z+random.uniform(-3,3), -random.uniform(0.3,1.0), 1.0
                    ])
        # Atualiza a física do splash d'água
        ns = []
        for sp in self.splash:
            sp[3] += 0.06; sp[1] += sp[3]; sp[4] -= 0.04
            if sp[4] > 0: ns.append(sp)
        self.splash = ns

class Abelha:
    """Controla o voo suave de abelhas e vagalumes."""
    def __init__(self, cx, cz):
        self.cx = cx + random.uniform(-15, 15) # Centro do raio de voo
        self.cz = cz + random.uniform(-15, 15)
        self.fase = random.uniform(0, 6.28)    # Posição inicial no círculo (0 a 2*PI)
        self.raio = random.uniform(8, 18)      # Quão longe do centro ela voa
        self.vel = random.uniform(0.003, 0.008)# Velocidade circular
        self.alt = random.uniform(14, 26)      # Altura do voo
        self.wv = random.uniform(0.4, 0.7)     # Velocidade de batida das asas
        self.reposition_timer = random.randint(400, 900)

    def update(self):
        self.fase += self.vel
        self.reposition_timer -= 1
        # De tempos em tempos, a abelha escolhe outra flor para orbitar
        if self.reposition_timer <= 0:
            idx = random.randint(0, len(flores)-1)
            self.cx = flores[idx]["x"] + random.uniform(-20, 20)
            self.cz = flores[idx]["z"] + random.uniform(-20, 20)
            self.reposition_timer = random.randint(400, 900)

# =========================================================
# SETUP (Executado apenas 1 vez ao rodar o script)
# =========================================================
def setup():
    # Declarando globais que serão inicializadas aqui
    global tex_grama, tex_parede, tex_madeira, tex_terra, tex_telhados
    global obstaculos, chamine_pos, pedras_rio, peixes, abelhas

    createCanvas(900, 700, WEBGL) # Inicializa o motor 3D
    noStroke()                    # Remove as linhas de contorno padrão dos polígonos
    textureMode(NORMAL)           # Permite mapear texturas usando valores de 0 a 1 (UV mapping)

    # ---------------------------------------------------------
    # GERAÇÃO PROCEDURAL DE TEXTURAS (Pinta em 2D e usa como pele do 3D)
    # ---------------------------------------------------------
    
    # Textura de Grama: Fundo verde e várias bolinhas aleatórias para simular folhas
    tex_grama = createGraphics(128, 128)
    tex_grama.background(80, 220, 60)
    tex_grama.noStroke()
    for i in range(70):
        tex_grama.fill(70+random.randint(-15,15), 210+random.randint(-18,18), 50+random.randint(-15,15))
        tex_grama.circle(random.randint(0,128), random.randint(0,128), random.randint(3,9))

    # Textura de Parede de Gesso: Linhas horizontais sutis e pontinhos esfumaçados
    tex_parede = createGraphics(256, 256)
    tex_parede.background(255, 248, 232)
    tex_parede.stroke(230, 215, 192); tex_parede.strokeWeight(1.5); tex_parede.noFill()
    for i in range(0, 256, 16): tex_parede.line(0, i, 256, i)
    tex_parede.noStroke()
    for i in range(25):
        tex_parede.fill(248, 240, 222, 90)
        tex_parede.circle(random.randint(0,256), random.randint(0,256), random.randint(6,16))

    # Textura de Madeira: Linhas verticais simulando os veios da madeira
    tex_madeira = createGraphics(128, 128)
    tex_madeira.background(185, 138, 92); tex_madeira.stroke(168, 120, 75); tex_madeira.strokeWeight(2)
    for i in range(25): tex_madeira.line(random.randint(0,128), 0, random.randint(0,128), 128)

    # Textura de Terra (Rua): Bolinhas marrons para simular pedregulhos
    tex_terra = createGraphics(128, 128)
    tex_terra.background(178, 148, 108); tex_terra.noStroke()
    for i in range(80):
        tex_terra.fill(165+random.randint(-18,18), 135+random.randint(-18,18), 95+random.randint(-18,18))
        tex_terra.circle(random.randint(0,128), random.randint(0,128), random.randint(2,7))

    # Telhados: Loop aninhado desenhando arcos (arc) para criar o visual de telhas sobrepostas
    tex_telhados = []
    for c in casas:
        cr, cg, cb = c["cor"] # Extrai a cor específica da casa
        t = createGraphics(128, 128); t.background(cr, cg, cb); t.noFill()
        t.stroke(max(0,cr-22), max(0,cg-22), max(0,cb-22)); t.strokeWeight(2.5)
        for y in range(0, 140, 18):
            for x in range(-10, 140, 18):
                off = 9 if (y//18) % 2 == 0 else 0 # Deslocamento alternado (como tijolos)
                t.arc(x+off, y, 18, 18, 0, PI)
        tex_telhados.append(t)

    # ---------------------------------------------------------
    # CÁLCULOS MATEMÁTICOS INICIAIS
    # ---------------------------------------------------------
    
    # Cria os Boundaries (Bounding Boxes) das casas para colisões do coelho
    obstaculos = []
    for c in casas:
        hw, hd = 60 * c["e"], 50 * c["e"] # Calcula metade da largura (hw) e profundidade (hd)
        if abs(abs(c["r"]) - 1.5708) < 0.3: hw, hd = hd, hw # Inverte se a casa estiver rodada 90 graus
        obstaculos.append({"x1":c["x"]-hw-5,"x2":c["x"]+hw+5,"z1":c["z"]-hd-5,"z2":c["z"]+hd+5})

    # Calcula onde fica exatamente o topo da chaminé usando trigonometria
    chamine_pos = []
    for c in casas:
        e, r = c["e"], c["r"]
        if c["ch"]:
            # Rotação polar para achar o deslocamento relativo da chaminé
            px = c["x"] + e*(35*cos(r) - 20*sin(r))
            py = CHAO_Y - 40*e - 82*e
            pz = c["z"] + e*(-35*sin(r) - 20*cos(r))
        else:
            px = c["x"]
            py = CHAO_Y - 40*e - 65*e 
            pz = c["z"]
            
        chamine_pos.append({
            "x": px, "y": py, "z": pz, "tipo": c["smoke"]
        })

    # Distrubui as pedrinhas da margem do rio usando função seno para criar curvas orgânicas
    pedras_rio = []
    for i in range(13):
        pedras_rio.append({
            "x": -160+i*26+sin(i*4.1)*8,
            "z": RIO_Z+(RIO_W/2+4)*(1 if i%2==0 else -1)+sin(i*2.7)*3,
            "s": 2.5+abs(sin(i*1.3))*3
        })

    peixes = [Peixe() for _ in range(4)]
    abelhas = [Abelha(f["x"], f["z"]) for f in flores[:4]]
    abelhas.append(Abelha(-55, 42))

# =========================================================
# DRAW PRINCIPAL (Executado 60 vezes por segundo)
# =========================================================
def draw():
    global giro_camera, tempo_dia, fumaca, ESCALA

    # INTERATIVIDADE DO MOUSE PARA O HUD (Interface)
    if mouseIsPressed:
        if mouseX > width - 70:
            # Controla a barra de dia/noite da direita mapeando a posição do Y do mouse
            td = remap(mouseY, 230, 470, 0, 1)
            tempo_dia = max(0, min(1, td))
        elif mouseX < 100:
            # Lógica dos botões esquerdos usando cálculo de distância (dist)
            if dist(mouseX, mouseY, 50, height/2 - 40) < 20: ESCALA = min(2.5, ESCALA + 0.02) # Zoom in
            if dist(mouseX, mouseY, 50, height/2 + 20) < 20: ESCALA = max(0.8, ESCALA - 0.02) # Zoom out
            if dist(mouseX, mouseY, 25, height - 80) < 25: giro_camera += 0.03 # Roda p/ esquerda
            if dist(mouseX, mouseY, 75, height - 80) < 25: giro_camera -= 0.03 # Roda p/ direita

    # MATEMÁTICA DO CLIMA
    # Transforma o tempo (0 a 1) num ciclo circular de radianos (PI/2 a 3PI/2)
    ciclo = remap(tempo_dia, 0, 1, PI/2, 3*PI/2)
    # A altura do sol é o Seno desse ciclo (-1 é fundo, +1 é pino do meio dia)
    alt_sol = max(-1.0, min(sin(ciclo), 0.94))

    # Paletas de cor (Dia, Tarde, Noite)
    C_DIA=(140, 205, 230); C_TAR=(255, 130, 85); C_NOI=(18, 28, 55) # Céu
    L_DIA=(255, 248, 210); L_TAR=(255, 155, 85); L_NOI=(22, 32, 65) # Luz do Sol/Lua

    # Interpolação linear de cor baseada na altura do sol
    if alt_sol > 0.2:
        t = remap(alt_sol, 0.2, 1.0, 1, 0)
        ceu = cor_mix(C_DIA, C_TAR, t); luz = cor_mix(L_DIA, L_TAR, t)
    else:
        t = remap(alt_sol, -1.0, 0.2, 1, 0)
        ceu = cor_mix(C_TAR, C_NOI, t); luz = cor_mix(L_TAR, L_NOI, t)

    background(*ceu) # Pinta o fundo da cena
    
    # ---------------------------------------------------------
    # ILUMINAÇÃO DA CENA 3D
    # ---------------------------------------------------------
    
    # Luz Ambiente reflete em todas as superfícies (evita áreas 100% pretas)
    ambientLight(luz[0]*0.60, luz[1]*0.60, luz[2]*0.60)

    # Luz do sol (Direcional). Só funciona se o sol estiver "acima" do chão (alt_sol > 0)
    if alt_sol > 0:
        inte = max(0, min(1, remap(alt_sol, 0, 0.15, 0, 1))) # Fade suave no amanhecer
        inte = inte * 0.75 # Limita a força máxima pra evitar superexposição (branco estourado)
        # O vetor -cos(ciclo), alt_sol define a angulação natural do sol de um lado pro outro do céu!
        directionalLight(luz[0]*inte, luz[1]*inte, luz[2]*inte, -cos(ciclo)-0.2, alt_sol+0.3, -0.8)

    noite = alt_sol < 0.1 # Booleano prático para saber se já escureceu
    
    if noite:
        # Preenchimento fraco e azulado noturno vindo do fundo, pra impedir sombras negras absolutas
        directionalLight(30, 40, 60, 0, -0.2, 1.0) 
    
    mover_coelho_teclado() # Resolve a física antes de desenhar a tela

    # Gerenciador de emissão de partículas (12% de chance por frame de spawnar fumaça)
    for cp in chamine_pos:
        if random.random() < 0.12: fumaca.append(Particula(cp["x"], cp["y"], cp["z"], cp["tipo"]))
    for p in fumaca:
        p.y -= p.vy; p.x += p.vx; p.z += p.vz; p.vida -= p.dec; p.tam += 0.07 # Física
    fumaca = [p for p in fumaca if p.vida > 0] # Remove partículas velhas

    for px in peixes: px.update()
    for b in abelhas: b.update()

    # =========================================================
    # RENDERIZAÇÃO DO MUNDO 3D (Câmera)
    # =========================================================
    push() # Salva a matriz original. Tudo daqui em diante é movido junto pela câmera
    scale(ESCALA)
    rotateX(CAM_ANGULO) # Tomba a câmera para baixo
    rotateY(giro_camera) # Rotaciona o lote inteiro
    noStroke()

    # DESENHANDO SÓLIDOS

    if noite:
        # As PointLights são fontes de luz omnidirecionais saindo dos postes
        for p in postes:
            pointLight(140, 95, 25, p["x"], CHAO_Y-45, p["z"])

    desenha_terreno()
    desenha_ruas()
    desenha_riacho()

    for i, c in enumerate(casas):
        desenha_casa(c["x"], c["z"], tex_telhados[i], c["e"], c["r"], c["ch"], noite, c["sh"])

    for p in postes: desenha_poste_solido(p["x"], p["z"], noite)
    for a in arvores: desenha_arvore(a["x"], a["z"], a["h"])
    for f in flores: desenha_flores_cluster(f["x"], f["z"])
    for a in arbs: desenha_arbusto(a["x"], a["z"], a["s"])

    desenha_coelhinho()

    # DESENHANDO OBJETOS TRANSLÚCIDOS E BRILHOS 
    for p in postes: desenha_poste_brilho(p["x"], p["z"], noite)
    for px in peixes: desenha_peixe(px)
    for b in abelhas: desenha_abelha(b, noite)
    desenha_fumaca_3d()
    
    pop() # Restaura a matriz original, saindo do modo câmera giratória.

    # DESENHA A INTERFACE 2D (HUD)
    # Por estar fora do push()/pop() da câmera, a interface não sofre zoom nem rotaciona.
    desenha_hud(noite, alt_sol)

# =========================================================
# LÓGICA DO COELHO VIA TECLADO (Sincronizado com a Câmera)
# =========================================================
def mover_coelho_teclado():
    global coelho_x, coelho_z, coelho_dir, coelho_anda

    bx, bz = 0, 0
    andando = False

    # 1. Lê a intenção do jogador em relação à TELA
    if keyIsDown(UP_ARROW):    bz -= COELHO_V; andando = True
    if keyIsDown(DOWN_ARROW):  bz += COELHO_V; andando = True
    if keyIsDown(LEFT_ARROW):  bx -= COELHO_V; andando = True
    if keyIsDown(RIGHT_ARROW): bx += COELHO_V; andando = True

    if andando:
        coelho_anda = True
        
        # 2. Matriz de Rotação 2D
        # Pega a intenção da tela (bx, bz) e gira ela conforme o ângulo da câmera
        # Isso garante que "para cima" sempre mova para o fundo da tela visualmente.
        ca = cos(giro_camera)
        sa = sin(giro_camera)
        dx = bx * ca - bz * sa
        dz = bx * sa + bz * ca

        # 3. Interpola a rotação do corpo do coelho (Suavização com atan2)
        alvo = atan2(dx, dz)
        diff = alvo - coelho_dir
        while diff > PI: diff -= TAU
        while diff < -PI: diff += TAU
        coelho_dir += diff * 0.2

        nx, nz = coelho_x + dx, coelho_z + dz

        # 4. Checagem de Colisão (Sliding Axis)
        # Se bater na parede, testa X e Z separados para ele "escorregar" pelas bordas
        if not colide(nx, nz, COELHO_R):
            coelho_x, coelho_z = nx, nz
        else:
            if not colide(nx, coelho_z, COELHO_R): coelho_x = nx
            elif not colide(coelho_x, nz, COELHO_R): coelho_z = nz

        # 5. Limites do mapa (Clamp)
        coelho_x = max(-180, min(180, coelho_x))
        coelho_z = max(-90, min(150, coelho_z)) 
    else:
        coelho_anda = False

def colide(px, pz, r):
    """Verifica se um ponto (px, pz) e seu raio (r) estão dentro de algum obstáculo AABB."""
    for o in obstaculos:
        if px+r>o["x1"] and px-r<o["x2"] and pz+r>o["z1"] and pz-r<o["z2"]: return True
    return False

# =========================================================
# TERRENO E RUAS
# =========================================================
def desenha_terreno():
    push()
    translate(0, CHAO_Y+5, 0)
    ambientMaterial(255) # O material branco reflete a cor verdadeira da textura sob a luz
    texture(tex_grama)
    box(360, 10, 320) 
    pop()
    
    # Camada de sujeira decorativa abaixo da grama
    push()
    translate(0, CHAO_Y+12, 0)
    ambientMaterial(142, 108, 68)
    box(366, 6, 326)
    pop()

def desenha_ruas():
    for r in ruas:
        push(); translate(r["cx"], CHAO_Y-0.5, r["cz"])
        ambientMaterial(255); texture(tex_terra); box(r["w"], 2, r["d"]); pop()
    ambientMaterial(195, 180, 160)
    
    # Desenha pedrinhas decorativas usando função de seno para um padrão orgânico
    for i in range(8):
        push(); px = -65 + i * 22 + sin(i*3.7)*4
        translate(px, CHAO_Y-1.2, -8 + sin(i*2.1)*5); box(5+sin(i)*1.5, 1, 4+cos(i)*1); pop()

# =========================================================
# RIACHO
# =========================================================
def desenha_riacho():
    push()
    translate(0, CHAO_Y-1, RIO_Z)
    ambientMaterial(20, 130, 225) 
    box(360, 4, RIO_W+6) 
    
    # Loop desenhando faixas de água claras deslizando 
    for i in range(14):
        push(); xo = -160 + i*25; w = sin(frameCount*0.025 + i*0.7)*1.0; translate(xo, -2.5+w, 0)
        bv = 190 + sin(frameCount*0.02 + i*0.5)*20
        fill(30, 150+sin(frameCount*0.015+i)*12, bv, 160); box(28, 1.5, RIO_W-3); pop()
    
    # Loop de bolinhas de espuma brancas
    for i in range(6):
        push(); fx = -160+i*60 + sin(frameCount*0.012+i*2)*15; fz = sin(frameCount*0.01+i*3)*6
        translate(fx, -3.5, fz); fill(255,255,255, 50+sin(frameCount*0.03+i)*18); sphere(1.5); pop()
    pop()
    
    ambientMaterial(120, 110, 95)
    for p in pedras_rio:
        push(); translate(p["x"], CHAO_Y-1, p["z"]); sphere(p["s"]); pop()
        
    for i in range(8):
        push(); rx = -160 + i*45 + sin(i*3.2)*6; rz = RIO_Z + (RIO_W/2+6)*(1 if i%2==0 else -1)
        translate(rx, CHAO_Y, rz); ambientMaterial(72, 135, 48); box(1, 10, 1) # Caule
        translate(0, -6, 0); ambientMaterial(95, 165, 55); sphere(1.8); pop()  # Flor

# =========================================================
# CASA
# =========================================================
def desenha_casa(x, z, tex_roof, esc, rot, tem_ch, noite, sh_cor):
    push(); translate(x, CHAO_Y - 40*esc, z); rotateY(rot); scale(esc)
    hw, hh, hd = 60, 40, 50

    ambientMaterial(255); texture(tex_parede)
    # A função utilitária pq() precisa receber as normais de cada face 
    # (direção ortogonal) para o modelo de iluminação calcular o sombreamento corretamente
    pq(0,0,1,   -hw,-hh,hd,  hw,-hh,hd,   hw,hh,hd,   -hw,hh,hd)    # Face Frente
    pq(0,0,-1,  hw,-hh,-hd,  -hw,-hh,-hd, -hw,hh,-hd, hw,hh,-hd)    # Face Trás
    pq(1,0,0,   hw,-hh,hd,   hw,-hh,-hd,  hw,hh,-hd,  hw,hh,hd)     # Face Direita
    pq(-1,0,0,  -hw,-hh,-hd, -hw,-hh,hd,  -hw,hh,hd,  -hw,hh,-hd)   # Face Esquerda

    push(); translate(0, -hh, 0); ambientMaterial(255); texture(tex_roof)
    bx, bz, ty = 65, 55, -48
    
    # Desenhando as faces do telhado manualmente (Prisma). Normais apontam diagonalmente para cima.
    beginShape(TRIANGLES); normal(0, -0.7, 0.7); vertex(-bx,0,bz,0,1); vertex(bx,0,bz,1,1); vertex(0,ty,0,0.5,0); endShape()
    beginShape(TRIANGLES); normal(0.7, -0.7, 0); vertex(bx,0,bz,0,1); vertex(bx,0,-bz,1,1); vertex(0,ty,0,0.5,0); endShape()
    beginShape(TRIANGLES); normal(0, -0.7, -0.7); vertex(bx,0,-bz,0,1); vertex(-bx,0,-bz,1,1); vertex(0,ty,0,0.5,0); endShape()
    beginShape(TRIANGLES); normal(-0.7, -0.7, 0); vertex(-bx,0,-bz,0,1); vertex(-bx,0,bz,1,1); vertex(0,ty,0,0.5,0); endShape()
    # A base do telhado fechando a malha
    beginShape(QUADS); normal(0, 1, 0); vertex(-bx,0,bz,0,1); vertex(bx,0,bz,1,1); vertex(bx,0,-bz,1,0); vertex(-bx,0,-bz,0,0); endShape()
    pop()

    if tem_ch:
        push(); translate(35, -60, -20); ambientMaterial(188, 118, 88); box(14, 38, 14) # Tijolo
        translate(0, -19, 0); ambientMaterial(168, 98, 68); box(17, 5, 17); pop()       # Topo cinza

    push(); translate(0, hh-2, hd+5); ambientMaterial(185, 142, 102); box(38, 4, 10); pop() # Degrau
    
    # Porta principal
    push(); translate(0, 12, hd+1); ambientMaterial(255); box(30, 48, 2)
    translate(0, 0, 1); ambientMaterial(255); texture(tex_madeira); box(24, 44, 2)
    translate(7, 0, 2); ambientMaterial(255, 215, 45); sphere(2); pop() # Maçaneta

    _jan(-35, -5, hd+1, noite, sh_cor)
    _jan(35, -5, hd+1, noite, sh_cor)
    pop()

def _jan(x, y, z, noite, sh_cor):
    """Monta a estrutura complexa de uma janela (vidro, caixilho, persiana e floreira)."""
    push(); translate(x, y, z); ambientMaterial(255); box(24, 24, 2); translate(0, 0, 1)
    
    if noite: emissiveMaterial(255, 190, 40); ambientMaterial(255, 190, 40) # Brilha amarelo à noite
    else: ambientMaterial(168, 222, 240) # Azul celeste de dia
    
    box(18, 18, 2); translate(0, 0, 1); ambientMaterial(255); emissiveMaterial(0, 0, 0)
    box(18, 2.5, 1); box(2.5, 18, 1) # Cruz de madeira do vidro

    ambientMaterial(*sh_cor)
    push(); translate(-14, 0, -1); box(4, 22, 1.5); pop() # Persiana esq
    push(); translate(14, 0, -1); box(4, 22, 1.5); pop()  # Persiana dir

    # Vasinho de flores na janela
    push(); translate(0, 14, 2); ambientMaterial(138, 88, 52); box(20, 3.5, 5)
    ambientMaterial(255, 165, 185); push(); translate(-5,-2.5,0); sphere(1.8); pop()
    ambientMaterial(255, 215, 105); push(); translate(2,-2.5,0); sphere(1.8); pop()
    ambientMaterial(85, 162, 55); push(); translate(-1.5,-2,0); sphere(1.2); pop()
    pop(); pop()

# =========================================================
# POSTE 
# =========================================================
def desenha_poste_solido(x, z, noite):
    """Desenha a geometria de ferro do poste."""
    push(); translate(x, CHAO_Y, z); ambientMaterial(52, 48, 42)
    push(); translate(0,-22,0); box(3,44,3); pop()
    push(); translate(0,-2,0); ambientMaterial(42,38,32); box(8,4,8); pop()
    push(); translate(0,-42,0); ambientMaterial(62,55,48); box(5,3,5); pop()
    push(); translate(0,-44,0); box(2,5,2); pop()
    
    push(); translate(0, -48, 0)
    if noite:
        # A lâmpada propriamente dita (que emite luz)
        emissiveMaterial(255, 200, 50); ambientMaterial(255, 220, 80); sphere(3.5)
        emissiveMaterial(0, 0, 0) # Reseta emissão pro resto não brilhar
    else:
        ambientMaterial(198, 188, 158); sphere(3)
    pop(); pop()

def desenha_poste_brilho(x, z, noite):
    """Desenha as esferas transparentes que simulam ofuscamento da lente (glow)."""
    if noite:
        push(); translate(x, CHAO_Y - 48, z)
        # Esferas sobrepostas com canal Alpha decrescente
        fill(255, 215, 70, 32); sphere(7)
        fill(255, 210, 60, 18); sphere(12)
        fill(255, 200, 50, 8); sphere(18)
        pop()

# =========================================================
# COELHINHO
# =========================================================
def desenha_coelhinho():
    # Adiciona um movimento de "pulo" no eixo Y baseado no tempo apenas se estiver andando
    bounce = sin(frameCount*0.3)*2.5 if coelho_anda else 0
    push(); translate(coelho_x, CHAO_Y-12+bounce, coelho_z); rotateY(coelho_dir)

    ambientMaterial(255, 208, 218) # Rosa claro padrão
    push(); scale(1,1.15,1); sphere(9); pop() # Alonga a esfera do corpo

    push(); translate(0, -14, 0); ambientMaterial(255, 215, 222); sphere(7.5)  # Cabeça
    
    # Orelhas feitas de box() rotacionados com interior mais escuro
    push(); translate(-3.5,-9,-1); rotateZ(-0.15)
    ambientMaterial(255,208,218); box(3.8,13,2); ambientMaterial(255,158,178); box(2,9,1); pop()
    push(); translate(3.5,-9,-1); rotateZ(0.15)
    ambientMaterial(255,208,218); box(3.8,13,2); ambientMaterial(255,158,178); box(2,9,1); pop()

    ambientMaterial(25,25,25) # Olhos escuros
    push(); translate(-3,0,6); sphere(1.8); pop()
    push(); translate(3,0,6); sphere(1.8); pop()
    
    ambientMaterial(180) # Pontinho de reflexo no olho (fofo, sem brilho agressivo emissivo)
    push(); translate(-2.3,-0.8,7); sphere(0.4); pop()
    push(); translate(3.7,-0.8,7); sphere(0.4); pop()

    ambientMaterial(255,140,160); push(); translate(0,2.5,6.5); sphere(1.2); pop() # Nariz
    fill(255,162,182,80); push(); translate(-5,2,4); sphere(2); pop(); push(); translate(5,2,4); sphere(2); pop() # Blush translúcido
    pop() # Fim Cabeça

    push(); translate(0,-2,-9); ambientMaterial(255,242,248); sphere(3.5); pop() # Rabinho fofinho nas costas

    ambientMaterial(255,192,202) 
    push(); translate(-5,8,2); box(4,3,5); pop(); push(); translate(5,8,2); box(4,3,5); pop() # Patinhas do pé

    ambientMaterial(255,202,212) 
    # Animação dos braços balançando usando seno se estiver andando
    arm = sin(frameCount*0.3)*0.3 if coelho_anda else 0
    push(); translate(-9,-3,0); rotateX(arm); sphere(3); pop()
    push(); translate(9,-3,0); rotateX(-arm); sphere(3); pop()
    pop() # Fim coelho

# =========================================================
# VEGETACAO
# =========================================================
def desenha_arvore(x, z, h):
    push(); translate(x, CHAO_Y, z)
    ambientMaterial(135,92,55); push(); translate(0,-h*0.3,0); box(5,h*0.55,5); pop() # Tronco
    # Três blocos esféricos formando a copa da árvore folhuda
    ambientMaterial(72,162,62); push(); translate(0,-h*0.72,0); sphere(h*0.35); pop() 
    ambientMaterial(88,178,68); push(); translate(-4,-h*0.6,3); sphere(h*0.24); pop()
    ambientMaterial(62,152,55); push(); translate(3,-h*0.65,-3); sphere(h*0.27); pop()
    
    # Coloca frutinhas (maças vermelhas) apenas nas árvores localizadas do lado esquerdo (x < 0)
    if x < 0:
        ambientMaterial(255, 80, 80)
        push(); translate(h*0.15, -h*0.62, h*0.12); sphere(1.5); pop()
        push(); translate(-h*0.1, -h*0.58, -h*0.1); sphere(1.5); pop()
    pop()

def desenha_flores_cluster(x, z):
    cores = [(255,185,205),(255,225,125),(205,165,255),(255,155,185),(185,232,255)]
    push(); translate(x, CHAO_Y, z)
    for i in range(4): # 4 florzinhas juntas em círculo
        push(); fx, fz = sin(i*2.3+x*0.1)*8, cos(i*3.1+z*0.1)*8; translate(fx, 0, fz)
        ambientMaterial(78,158,48); push(); translate(0,-3,0); box(1,6,1); pop()
        ambientMaterial(*cores[i%len(cores)]); push(); translate(0,-6.5,0); sphere(2.5) # Cor puxada da lista
        ambientMaterial(255,255,198); sphere(1); pop(); pop() # Miolo amarelo
    pop()

def desenha_arbusto(x, z, s):
    # Cluster de esferas com pequenas florezinhas encravadas no meio
    push(); translate(x, CHAO_Y, z)
    ambientMaterial(88,172,78); push(); translate(0,-s*0.5,0); sphere(s); pop()
    ambientMaterial(78,162,68); push(); translate(-s*0.5,-s*0.3,s*0.3); sphere(s*0.7); pop()
    ambientMaterial(98,178,82); push(); translate(s*0.4,-s*0.4,-s*0.3); sphere(s*0.75); pop()
    ambientMaterial(255, 220, 240); push(); translate(s*0.3, -s*0.7, s*0.2); sphere(1.2); pop()
    ambientMaterial(255, 240, 200); push(); translate(-s*0.4, -s*0.6, -s*0.1); sphere(1.0); pop()
    pop()

# =========================================================
# ANIMAÇÕES EXTRAS
# =========================================================
def desenha_peixe(p):
    # Gotas d'água ao cair
    for sp in p.splash:
        push(); translate(sp[0],sp[1],sp[2])
        fill(148,208,255, int(sp[4]*180)); sphere(1); pop()
    
    if p.fase != 1: return # Não desenha o corpo se estiver embaixo d'água
    
    push(); translate(p.x, p.y, p.z); rotateZ(p.rot)
    fill(p.cor[0],p.cor[1],p.cor[2])
    push(); scale(0.8, 0.4, 0.4); sphere(p.tam); pop() # Corpo elipsóide laranja
    
    # Cauda triangular
    push(); translate(-p.tam*0.7,0,0)
    fill(max(0,p.cor[0]-30),max(0,p.cor[1]-30),max(0,p.cor[2]-30)); rotateZ(sin(frameCount*0.2)*0.2)
    beginShape(TRIANGLES); vertex(0,-p.tam*0.25,0); vertex(0,p.tam*0.25,0); vertex(-p.tam*0.5,0,0); endShape(); pop()
    
    fill(255); push(); translate(p.tam*0.4,-1,p.tam*0.25); sphere(0.8); fill(0); sphere(0.4); pop(); pop() # Olho

def desenha_abelha(b, noite):
    bx, bz, by = b.cx + cos(b.fase)*b.raio, b.cz + sin(b.fase)*b.raio, CHAO_Y - b.alt + sin(frameCount*0.02 + b.fase)*3
    push(); translate(bx, by, bz)
    
    if noite:
        # Se for noite, as abelhas se comportam visualmente como vagalumes (ponto de luz brilhante)
        glow = sin(frameCount*0.04 + b.fase)*0.4 + 0.6
        emissiveMaterial(180, 190, 40); ambientMaterial(220, 230, 80); sphere(0.8 + glow*0.3)
        emissiveMaterial(0, 0, 0); fill(220, 235, 70, 22); sphere(3 + glow)
        fill(210, 225, 60, 8); sphere(6 + glow*1.5)
    else:
        # Abelhinha gordinha de dia
        rotateY(-b.fase) # Vira para o sentido do giro
        ambientMaterial(255, 204, 0)
        push(); scale(1.2, 0.8, 0.8); sphere(1.5); pop() # Corpo amarelo
        ambientMaterial(30, 30, 30)
        push(); scale(0.5, 0.85, 0.85); sphere(1.55); pop() # Listra preta
        
        # Asas translúcidas vibrando rápido
        wing = sin(frameCount*b.wv)*0.6
        fill(255, 255, 255, 200)
        push(); translate(0, -1, 0.5); rotateX(wing); scale(0.8, 0.1, 1.5); sphere(1); pop()
        push(); translate(0, -1, -0.5); rotateX(-wing); scale(0.8, 0.1, 1.5); sphere(1); pop()
    pop()

def desenha_fumaca_3d():
    # Desenhado por último pois é translúcido
    for p in fumaca:
        push(); translate(p.x, p.y, p.z)
        alpha_base = 125 if p.tipo == "normal" else 40 # Lê a propriedade pra saber a opacidade máxima
        fill(198, 198, 198, int(p.vida * alpha_base))  # Aplica o canal Alpha (transparência)
        sphere(p.tam)
        pop()

# =========================================================
# HUD (Interface de Usuário)
# =========================================================
def desenha_hud(noite, alt_sol):
    # resetMatrix e ortho garantem que estamos desenhando "2D colado no vidro da tela", sem perspectiva 3D
    push(); resetMatrix(); ortho(); translate(-width/2, -height/2, 0); noLights(); noStroke()
    
    # Efeito de estrelinhas de fundo na tela cheia à noite
    if noite:
        fill(255,255,218, max(0, remap(alt_sol, 0.1, -0.3, 0, 180)))
        for i in range(18):
            circle(width/2 + sin(i*7.3+1.2)*380, sin(i*4.1+2.5)*80 + 60, 1+(sin(frameCount*0.015+i*1.7)*0.5+0.5)*1.2)

    # --- BARRA LATERAL DIREITA (CONTROLE DO TEMPO) ---
    sl_x = width - 55
    fill(0,0,0,40); rectMode(CENTER); rect(sl_x, height/2, 8, 240, 4) # Fundo do slider
    
    # Sol e Linhas superiores
    fill(255,255,255,90); circle(sl_x, height/2-110, 34); fill(255,218,48); circle(sl_x, height/2-110, 18)
    stroke(255,218,48); strokeWeight(1.5)
    for i in range(8):
        a = i*QUARTER_PI; line(sl_x+cos(a)*12, height/2-110+sin(a)*12, sl_x+cos(a)*16, height/2-110+sin(a)*16)
    
    # Lua inferior
    noStroke()
    fill(255,255,255,90); circle(sl_x, height/2+110, 34); fill(195,195,215); circle(sl_x, height/2+110, 18)
    
    # Pino de arrasto
    fill(255); stroke(148); strokeWeight(2); circle(sl_x, remap(tempo_dia, 0, 1, height/2-95, height/2+95), 14)
    noStroke()

    # --- BARRA LATERAL ESQUERDA (CÂMERA E ZOOM) ---
    
    # Lupa Zoom In (+)
    fill(0,0,0,60); circle(50, height/2 - 40, 40)
    fill(255); rectMode(CENTER)
    rect(50, height/2 - 40, 16, 4, 2); rect(50, height/2 - 40, 4, 16, 2)
    
    # Lupa Zoom Out (-)
    fill(0,0,0,60); circle(50, height/2 + 20, 40)
    fill(255); rectMode(CENTER)
    rect(50, height/2 + 20, 16, 4, 2)

    # Manete/Joystick para Rotação da Maquete
    fill(0,0,0,60); circle(50, height - 80, 80)
    fill(255, 255, 255, 150)
    triangle(25, height-80, 40, height-90, 40, height-70) # Seta Esq
    triangle(75, height-80, 60, height-90, 60, height-70) # Seta Dir
    fill(255); circle(50, height - 80, 25) # Botão central
    
    pop()

# =========================================================
# UTILITARIOS MATEMÁTICOS
# =========================================================
def remap(v, a, b, c, d):
    """Mapeia o valor v da escala (a, b) para a escala (c, d) limitando os extremos."""
    if b==a: return c
    v=max(a,min(v,b))
    return c+(d-c)*((v-a)/(b-a))

def cor_mix(c1, c2, t): 
    """Interpolação Linear (Lerp) de Cores. Encontra a cor t% no meio entre c1 e c2."""
    return (c1[0]+(c2[0]-c1[0])*t, c1[1]+(c2[1]-c1[1])*t, c1[2]+(c2[2]-c1[2])*t)

def pq(nx, ny, nz, x0,y0,z0, x1,y1,z1, x2,y2,z2, x3,y3,z3):
    """Envolve a renderização de um Quadrilátero manual aplicando o Vetor Normal.
    Isso é vital para a Engine WEBGL saber como a luz deve rebater nas paredes do objeto."""
    beginShape(QUADS)
    normal(nx, ny, nz)
    vertex(x0,y0,z0,0,0); vertex(x1,y1,z1,1,0); vertex(x2,y2,z2,1,1); vertex(x3,y3,z3,0,1)
    endShape()