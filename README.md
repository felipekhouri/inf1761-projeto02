# Projeto 02 - Cena 3D com Mesa, Objetos e Iluminação Avançada

**Disciplina:** INF1761 – Computação Gráfica **Professor:** Waldemar Celes
**Aluno:** Felipe Khouri Gameleira (2011265) **Período:** 2025.2

---

## Descrição do Projeto

Neste projeto, implementei uma cena 3D interativa com uma mesa de madeira e
objetos sobre ela, usando o framework de grafo de cena fornecido pelo professor.
A ideia era criar uma cena realista com vários efeitos gráficos:

- Iluminação Phong por fragmento (fragment shader)
- Efeito de fog (neblina por distância)
- Mapeamento de texturas (madeira, papel)
- Bump mapping para simular rugosidade
- Câmera interativa com arcball
- Geometrias procedurais (cilindro e cone)

---

## Cena Implementada

### Objetos Renderizados

| Objeto            | Tipo              | Material | Textura          | Observações                       |
| ----------------- | ----------------- | -------- | ---------------- | --------------------------------- |
| Chão              | Cubo achatado     | Cinza    | —                | Base da cena                      |
| Mesa (tampo)      | Cubo achatado     | Madeira  | wood.jpg         | Superfície principal              |
| Mesa (pernas)     | 4 Cilindros       | Madeira  | wood.jpg         | Suporte estrutural                |
| Papel             | Cubo fino         | Branco   | paper.jpg        | Sobre a mesa                      |
| Xícara            | Cilindro oco      | Cinza    | —                | Sem tapa superior                 |
| Esfera verde      | Esfera            | Verde    | noise.png (bump) | Rugosidade simulada               |
| Luminária base    | Cilindro achatado | Azul     | —                | Apoio da lâmpada                  |
| Luminária haste 1 | Cilindro fino     | Azul     | —                | Vertical                          |
| Luminária haste 2 | Cilindro fino     | Azul     | —                | Inclinada 45°                     |
| Luminária cabeça  | Cone              | Azul     | —                | Inclinado 45°, visível por dentro |

---

## Arquitetura Técnica

### Estrutura de Diretórios

```
projeto02/
├── main.py                 # Programa principal
├── cone.py                 # Classe Cone (geometria procedural)
├── cylinder.py             # Classe Cylinder (geometria procedural)
├── README.md              # Este arquivo
├── shaders/
│   ├── phong.vert         # Vertex shader (Phong + texturas + bump)
│   └── phong.frag         # Fragment shader (Phong + fog + bump mapping)
└── texturas/
    ├── wood.jpg           # Textura de madeira (mesa e pernas)
    ├── paper.jpg          # Textura de papel
    └── noise.png          # Mapa de rugosidade (bump map)
```

### Classes Principais

#### Cone (`cone.py`)

Criei uma classe para gerar geometria de cone proceduralmente. O cone é definido
com:

- Parâmetros: `nslices` (subdivisões radiais), `with_base` (se tem tampa
  inferior), `disable_culling` (renderiza os dois lados)
- O vértice fica em +Y, a base em Y=0, raio=1
- Normais e coordenadas de textura calculadas corretamente

#### Cylinder (`cylinder.py`)

Implementei também um cilindro procedural com:

- Parâmetros: `nslices`, `nstacks` (subdivisões verticais), `with_caps` (tampas
  superior e inferior), `disable_culling`
- Base em Y=0, topo em Y=1, raio=1
- Mapeamento cilíndrico de texturas

---

## Recursos Implementados

### 1. Iluminação Phong por Fragmento

Implementei o modelo de Phong no fragment shader para que cada pixel da tela
fosse iluminado individualmente. O código calcula:

```glsl
// phong.frag - Modelo de iluminação
vec3 N = normalize(neye);
vec3 L = normalize(light);
vec3 V = normalize(-veye);
vec3 R = reflect(-L, N);

// Componentes de iluminação
vec4 color = mamb*lamb + mdif*ldif*max(dot(N,L), 0.0);
if (dot(N,L) > 0.0)
    color += mspe*lspe*pow(max(dot(R,V), 0.0), mshi);
```

- Componente ambiente (muito fraca)
- Componente difusa (a maior parte da iluminação)
- Componente especular (brilho)

### 2. Mapeamento de Texturas

Apliquei texturas em vários objetos:

- **Madeira**: na mesa (tampo + 4 pernas)
- **Papel**: objeto decorativo sobre a mesa
- **Noise.png**: bump map da esfera verde

### 3. Efeito de Fog (Neblina)

Implementei um fog exponencial que deixa a cena mais dramática:

```glsl
// phong.frag - Fog exponencial
if (useFog) {
    float fogFactor = exp(-0.3 * distance(veye, vec3(0.0)));
    color = mix(vec4(fogColor, 1.0), color, fogFactor);
}
```

- Cor preta, que combina com o fundo
- Fator de 0.3 (bem perceptível)
- Objetos distantes "desaparecem" na neblina

### 4. Bump Mapping (Rugosidade)

Usei bump mapping para criar uma ilusão de superfície rugosa na esfera verde:

```glsl
// phong.frag - Perturbação de normais
if (useBump) {
    float h = texture(bumpTex, texcoord).r;
    float scale = 0.05;
    vec3 dpdx = dFdx(vec3(texcoord, h * scale));
    vec3 dpdy = dFdy(vec3(texcoord, h * scale));
    vec3 normalBump = normalize(cross(dpdx, dpdy));
    N = normalize(mix(N, normalBump, 0.5));
}
```

- Usa derivadas parciais para calcular normais perturbadas
- Mistura com a normal original (50% blend)
- A textura noise.png fornece a altura

### 5. Câmera com Arcball

Usei a câmera do framework que já tinha suporte a arcball:

- Rotação interativa via mouse
- As rotações são suaves e intuitivas
- Classe `Camera3D` do `scene_graph` gerencia as transformações

---

## Como Executar

```bash
cd src
python main.py
```

---

## Visualização

A cena ficou assim:

- Ambiente bem escuro (fundo preto, luz ambiente mínima)
- Luminária azul como o principal foco de luz
- Fog preto que literalmente engole os objetos distantes
- Mesa com textura de madeira bem realista
- Esfera verde com bump mapping visível (dá pra ver que tem textura)
- Iluminação Phong cria sombras bem naturais

### Screenshots

As capturas de tela da cena estão em **#file:prints**. Fiz screenshots de vários
ângulos para mostrar melhor como ficou.

---

## Iluminação

Configurei a luz assim:

```python
light = Light(0.65, 1.7, 0.3, 1.0, "world")
light.SetAmbient(0.01, 0.01, 0.01)      # Ambiente mínimo (quase preto)
light.SetDiffuse(3.0, 3.0, 3.0)         # Difusa bem forte
light.SetSpecular(1.0, 1.0, 1.0)        # Especular normal
```

## Notas Técnicas

### Geometrias Procedurais

Tanto o Cylinder quanto o Cone geram a geometria proceduralmente:

- Vértices, normais e coordenadas de textura são calculados no construtor
- Herdam de `Shape` do framework, que gerencia VAO/VBO automaticamente
- As texturas funcionam bem com os shaders Phong

### Sistema de Texturas

O framework (scene_graph) carrega e ativa texturas automaticamente:

- Classe `Texture` gerencia carregamento de arquivos de imagem
- Objetos sem textura recebem uma textura branca padrão
- Coordenadas de textura são interpoladas automaticamente no fragment shader

### Efeitos Avançados

- **Fog**: Implementado como pós-processamento no fragment shader
- **Bump mapping**: Usa derivadas parciais para calcular normais perturbadas
- Ambos podem ser ativados/desativados via uniforms booleanos

---

## Checklist de Entrega

- [x] Cena 3D com mesa e objetos
- [x] Iluminação Phong por fragmento
- [x] Texturas (madeira, papel, noise)
- [x] Fog (neblina)
- [x] Bump mapping (rugosidade)
- [x] Câmera com arcball
- [x] Classes procedurais (Cone, Cylinder)
- [x] Shaders atualizados
- [x] README.md completo
- [x] Screenshots em #file:prints
