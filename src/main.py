"""
Projeto 02 - INF1761 Computação Gráfica
Cena 3D com mesa, objetos, iluminação Phong, texturas, fog e bump mapping

Pontuação:
- Base (7.0 pts): mesa + objetos + iluminação
- Fog (1.0 pt): efeito de neblina por distância
- Bump mapping (2.0 pts): rugosidade na esfera verde
TOTAL: 10.0 pontos

Aluno: Felipe
Professor: Waldemar Celes (PUC-Rio)
"""

import glfw
from OpenGL.GL import *
import sys
import os

# Adiciona o diretório atual PRIMEIRO para usar nossos arquivos corrigidos
sys.path.insert(0, os.path.dirname(__file__))
# Adiciona o caminho do scene_graph como fallback
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "../scene_graph/python"))

import glm
from camera3d import Camera3D
from light import Light
from shader import Shader
from material import Material
from transform import Transform
from node import Node
from scene import Scene
from cube import Cube
from sphere import Sphere
from texture import Texture

# Importa geometrias customizadas
from cylinder import Cylinder
from cone import Cone

# posição inicial do observador
viewer_pos = glm.vec3(4.0, 3.5, 5.0)

# globais
scene = None
camera = None


def initialize(win):
    """Inicializa a cena 3D com mesa, objetos, fog e bump mapping"""
    global scene, camera

    # OpenGL
    glClearColor(0.0, 0.0, 0.0, 1.0)  # fundo PRETO (ambiente escuro)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)

    # ===== CÂMERA COM ARCBALL =====
    camera = Camera3D(viewer_pos[0], viewer_pos[1], viewer_pos[2])
    arcball = camera.CreateArcball()
    arcball.Attach(win)

    # ===== LUZ POSICIONAL PERTO DA LÂMPADA =====
    # Cabeça da lâmpada está em: (0.65, 1.9, 0.3)
    # Vamos posicionar a luz ABAIXO do cone, apontando para a mesa
    light = Light(0.65, 1.7, 0.3, 1.0, "world")  # Mais baixo, fora do cone
    light.SetAmbient(0.01, 0.01, 0.01)  # Mantém ambiente mínimo
    light.SetDiffuse(3.0, 3.0, 3.0)  # TRIPLICAR a intensidade difusa!
    light.SetSpecular(1.0, 1.0, 1.0)

    # ===== SHADER PHONG COM FOG E BUMP =====
    shader = Shader(light, "world")
    shader.AttachVertexShader("shaders/phong.vert")
    shader.AttachFragmentShader("shaders/phong.frag")
    shader.Link()

    # Configura fog (ativado globalmente)
    shader.UseProgram()
    fogColorLoc = glGetUniformLocation(shader.pid, "fogColor")
    useFogLoc = glGetUniformLocation(shader.pid, "useFog")
    useBumpLoc = glGetUniformLocation(shader.pid, "useBump")
    glUniform3f(fogColorLoc, 0.2, 0.2, 0.2)  # fog PRETO (ambiente escuro)
    glUniform1i(useFogLoc, 1)  # Ativa fog
    glUniform1i(useBumpLoc, 1)  # Ativa bump mapping

    # ===== MATERIAIS =====

    # Cinza para o chão
    mat_floor = Material(0.5, 0.5, 0.5, 1.0)
    mat_floor.SetSpecular(0.3, 0.3, 0.3, 1.0)
    mat_floor.SetShininess(16.0)

    # Material branco para objetos texturizados
    mat_white = Material(1.0, 1.0, 1.0, 1.0)
    mat_white.SetSpecular(0.5, 0.5, 0.5, 1.0)
    mat_white.SetShininess(32.0)

    # Verde para esfera com bump
    mat_green = Material(0.1, 0.8, 0.1, 1.0)
    mat_green.SetSpecular(1.0, 1.0, 1.0, 1.0)
    mat_green.SetShininess(64.0)

    # Cinza claro para a xícara
    mat_cup = Material(0.7, 0.7, 0.7, 1.0)
    mat_cup.SetSpecular(0.8, 0.8, 0.8, 1.0)
    mat_cup.SetShininess(128.0)

    # Azul para a lâmpada
    mat_blue = Material(0.1, 0.3, 0.8, 1.0)
    mat_blue.SetSpecular(1.0, 1.0, 1.0, 1.0)
    mat_blue.SetShininess(64.0)

    # ===== TEXTURAS =====
    # Textura branca padrão (1x1 pixel branco) para objetos sem textura
    tex_white = Texture("decal", None, glm.vec3(1.0, 1.0, 1.0))
    tex_wood = Texture("decal", "texturas/wood.jpg")
    tex_paper = Texture("decal", "texturas/paper.jpg")
    tex_noise = Texture("bumpTex", "texturas/noise.png")  # Para bump mapping

    # ===== GEOMETRIAS =====
    cube = Cube()
    sphere = Sphere(64, 64)
    cylinder = Cylinder(32, 1, True)  # Com tampas
    cylinder_no_cap = Cylinder(
        32, 1, False, True
    )  # Sem tampas, sem culling (xícara oca)
    cone = Cone(32, True, True)  # Com base, sem culling (luminária oca)

    # ===== CONSTRUÇÃO DA CENA =====

    # ===== CHÃO CINZA =====
    trf_floor = Transform()
    trf_floor.Translate(0.0, 0.0, 0.0)
    trf_floor.Scale(8.0, 0.1, 8.0)
    node_floor = Node(None, trf_floor, [mat_floor, tex_white], [cube])

    # ===== MESA (tampo + 4 pernas) =====

    # Tampo da mesa (tábua de madeira)
    trf_tampo = Transform()
    trf_tampo.Translate(0.0, 1.05, 0.0)  # Y = 1.05 (acima das pernas)
    trf_tampo.Scale(3.0, 0.1, 2.0)  # 3m largura, 0.1m espessura, 2m profundidade
    node_tampo = Node(None, trf_tampo, [mat_white, tex_wood], [cube])

    # Pernas da mesa (4 cilindros nos cantos)
    # Pernas: altura 0.7, centro em Y=0.35, Y ∈ [0.0, 0.7]
    # Tampo: Y ∈ [1.0, 1.1] (acima das pernas)
    # Deslocamento nos cantos: X = ±1.2, Z = ±0.8

    # Perna 1: (+X, +Z)
    trf_perna1 = Transform()
    trf_perna1.Translate(1.2, 0.3, 0.8)
    trf_perna1.Scale(0.1, 0.8, 0.1)
    node_perna1 = Node(None, trf_perna1, [mat_white, tex_wood], [cylinder])

    # Perna 2: (-X, +Z)
    trf_perna2 = Transform()
    trf_perna2.Translate(-1.2, 0.3, 0.8)
    trf_perna2.Scale(0.1, 0.8, 0.1)
    node_perna2 = Node(None, trf_perna2, [mat_white, tex_wood], [cylinder])

    # Perna 3: (+X, -Z)
    trf_perna3 = Transform()
    trf_perna3.Translate(1.2, 0.3, -0.8)
    trf_perna3.Scale(0.1, 0.8, 0.1)
    node_perna3 = Node(None, trf_perna3, [mat_white, tex_wood], [cylinder])

    # Perna 4: (-X, -Z)
    trf_perna4 = Transform()
    trf_perna4.Translate(-1.2, 0.3, -0.8)
    trf_perna4.Scale(0.1, 0.8, 0.1)
    node_perna4 = Node(None, trf_perna4, [mat_white, tex_wood], [cylinder])

    # ===== OBJETOS SOBRE A MESA =====
    # Superfície da mesa: Y = 1.1

    # PAPEL (cubo fino com textura de papel)
    trf_paper = Transform()
    trf_paper.Translate(-0.8, 1.11, 0.3)  # Y = 1.1 + 0.01 (metade da espessura)
    trf_paper.Scale(0.4, 0.02, 0.3)  # papel fino
    node_paper = Node(None, trf_paper, [mat_white, tex_paper], [cube])

    # XÍCARA (cilindro sem tampas)
    trf_cup = Transform()
    trf_cup.Translate(0.8, 1.2, -0.3)  # Y = 1.1 + 0.1 (metade da altura)
    trf_cup.Scale(0.15, 0.2, 0.15)  # xícara pequena
    node_cup = Node(None, trf_cup, [mat_cup, tex_white], [cylinder_no_cap])

    # ESFERA VERDE COM BUMP MAPPING (rugosidade com noise.png)
    trf_sphere_bump = Transform()
    trf_sphere_bump.Translate(-0.3, 1.4, -0.2)  # Y = 1.1 + 0.3 (raio)
    trf_sphere_bump.Scale(0.3, 0.3, 0.3)
    node_sphere_bump = Node(None, trf_sphere_bump, [mat_green, tex_noise], [sphere])

    # ===== LÂMPADA (base + haste vertical + haste inclinada + cabeça) =====
    # Posição base: (1.5, Y, 0.5) sobre a mesa

    # Base da lâmpada (cilindro achatado na mesa)
    trf_lamp_base = Transform()
    trf_lamp_base.Translate(1.15, 1.15, 0.5)  # Y = 1.1 + 0.01
    trf_lamp_base.Scale(0.2, 0.02, 0.2)
    node_lamp_base = Node(None, trf_lamp_base, [mat_blue, tex_white], [cylinder])

    # Haste 1 (vertical) - de Y=1.12 até Y=1.72
    trf_lamp_stem1 = Transform()
    trf_lamp_stem1.Translate(1.15, 1.15, 0.5)  # centro em Y=1.42
    trf_lamp_stem1.Scale(0.05, 0.6, 0.05)  # altura 0.6
    node_lamp_stem1 = Node(None, trf_lamp_stem1, [mat_blue, tex_white], [cylinder])

    # Haste 2 (inclinada 45°) - começa em (1.5, 1.72, 0.5)
    # Comprimento 0.5, inclinada 45° em Z
    # Δx ≈ 0.35, Δy ≈ 0.35
    # Centro: (1.675, 1.895, 0.5)
    trf_lamp_stem2 = Transform()
    trf_lamp_stem2.Translate(1.15, 1.75, 0.5)
    trf_lamp_stem2.Rotate(45.0, 0.0, 0.0, 1.0)  # inclina 45° em Z
    trf_lamp_stem2.Scale(0.05, 0.5, 0.05)
    node_lamp_stem2 = Node(None, trf_lamp_stem2, [mat_blue, tex_white], [cylinder])

    # Cabeça (cone invertido) - topo da haste 2: (1.85, 2.07, 0.5)
    trf_lamp_head = Transform()
    trf_lamp_head.Translate(0.65, 1.9, 0.3)
    trf_lamp_head.Rotate(45.0, 1.0, 0.0, 0.0)
    trf_lamp_head.Rotate(-35.0, 0.0, 0.0, 1.0)
    trf_lamp_head.Scale(0.25, 0.3, 0.25)
    node_lamp_head = Node(None, trf_lamp_head, [mat_blue, tex_white], [cone])

    # ===== MONTAGEM DO GRAFO DE CENA =====
    root = Node(
        shader,
        nodes=[
            node_floor,
            node_tampo,
            node_perna1,
            node_perna2,
            node_perna3,
            node_perna4,
            node_paper,
            node_cup,
            node_sphere_bump,
            node_lamp_base,
            node_lamp_stem1,
            node_lamp_stem2,
            node_lamp_head,
        ],
    )
    scene = Scene(root)


def display(win):
    """Renderiza a cena"""
    global scene, camera

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    if scene and camera:
        scene.Render(camera)


def keyboard(win, key, scancode, action, mods):
    """Callback de teclado para controles adicionais"""
    if action == glfw.PRESS and key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(win, True)


def main():
    """Função principal do programa"""

    # GLFW
    if not glfw.init():
        print("Erro ao inicializar GLFW")
        return

    # contexto OpenGL
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)

    # janela
    win = glfw.create_window(
        1024, 768, "Projeto 02 - Mesa com Fog e Bump Mapping", None, None
    )
    if not win:
        print("Erro ao criar janela GLFW")
        glfw.terminate()
        return

    # teclado
    glfw.set_key_callback(win, keyboard)

    # contexto da janela
    glfw.make_context_current(win)

    print("OpenGL version:", glGetString(GL_VERSION).decode("utf-8"))
    print("")
    print("PROJETO 02 - INF1761 Computação Gráfica")
    print("=" * 50)
    print("Pontuação:")
    print("  • Base (7.0 pts): Mesa + objetos + iluminação Phong")
    print("  • Fog (1.0 pt): Efeito de neblina por distância")
    print("  • Bump mapping (2.0 pts): Rugosidade na esfera verde")
    print("  TOTAL: 10.0 pontos")
    print("")
    print("CONTROLES:")
    print("  • Arraste com o mouse para rotacionar a cena (arcball)")
    print("  • ESC para sair")
    print("=" * 50)
    print("")

    # inicializa a cena
    initialize(win)

    # loop principal
    while not glfw.window_should_close(win):
        display(win)
        glfw.swap_buffers(win)
        glfw.poll_events()

    # finaliza GLFW
    glfw.terminate()


if __name__ == "__main__":
    main()
