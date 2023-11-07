from mplsoccer import VerticalPitch
import matplotlib.pyplot as plt

def write_text_on_labels_from_powerbi(positions, dataset, ax):
    for i, position in enumerate(positions, 1):
        x = position[0] * FIGWIDTH
        y = position[1] * FIGHEIGHT
        label = position[2]
        
        if label in dataset['code'].values:
            percent_value = dataset[dataset['code'] == label]['percent'].values[0]
            ax.scatter(x, y, color='red', s=200, zorder=2)
            ax.text(x, y + 4, f'{percent_value}%', color='white', ha='center', va='center', fontsize=12)
        else:
            ax.scatter(x, y, color='red', s=200, zorder=2)
        
        ax.text(x, y, str(i), color='white', ha='center', va='center', fontsize=12)
        ax.text(x, y - 4, label, color='white', ha='center', va='center', fontsize=12)

FIGWIDTH = 7
FIGHEIGHT = 8
NROWS = 1
NCOLS = 1
SPACE = 0
MAX_GRID = 1

PAD_TOP = 2
PAD_BOTTOM = 2
PAD_SIDES = ((120 + PAD_TOP + PAD_BOTTOM) * FIGWIDTH / FIGHEIGHT - 80) / 2
pitch = VerticalPitch(pad_top=PAD_TOP, pad_bottom=PAD_BOTTOM,
                      pad_left=PAD_SIDES, pad_right=PAD_SIDES,
                      pitch_color='grass', stripe=True, line_color='white')

GRID_WIDTH, GRID_HEIGHT = pitch.grid_dimensions(figwidth=FIGWIDTH, figheight=FIGHEIGHT,
                                                nrows=NROWS, ncols=NCOLS,
                                                max_grid=MAX_GRID, space=SPACE)
TITLE_HEIGHT = 0
ENDNOTE_HEIGHT = 0

fig, ax = pitch.grid(figheight=FIGHEIGHT, grid_width=GRID_WIDTH,
                     grid_height=GRID_HEIGHT, space=SPACE,
                     ncols=NCOLS, nrows=NROWS, title_height=TITLE_HEIGHT,
                     endnote_height=ENDNOTE_HEIGHT, axis=True)

LINHA_GR = 1
LINHA_DEFESAS_Y = 4
LINHA_MDC_Y = 6
LINHA_MC_Y = 7
LINHA_MO_Y = 9
LINHA_EXTREMOS_Y = 11
LINHA_PL_Y = 13

team_positions = [
                                                        (5.75, LINHA_GR, 'GR'),                                               # Posicao GR
    (10.5, LINHA_DEFESAS_Y, 'DD'), (7.5, LINHA_DEFESAS_Y, 'DC_D'), (4, LINHA_DEFESAS_Y, 'DC_E'), (1, LINHA_DEFESAS_Y, 'DE'),  # Posicao Defesas
                                   (7.5, LINHA_MDC_Y, 'MDC'),                                                                 # Posicao MDC
                                                                   (4, LINHA_MC_Y, 'MC'),                                     # Posicao MC
                                                        (5.75, LINHA_MO_Y, 'MO'),                                             # Posicao MO
                                                                                                 (1, LINHA_EXTREMOS_Y, 'EE'), # Posicao EE
                                                        (5.75, LINHA_PL_Y, 'PL'),                                             # Posicao PL
    (10.5, LINHA_EXTREMOS_Y, 'ED')                                                                                            # Posicao ED
]

write_text_on_labels_from_powerbi(team_positions, dataset, ax)

plt.show()
