from mplsoccer import VerticalPitch
import matplotlib.pyplot as plt

def write_text_on_labels_from_powerbi(positions, dataset, ax):
    dataset['code'] = dataset['code'].str.upper()

    for i, position in enumerate(positions, 1):
        x = position[0] * FIGWIDTH
        y = position[1] * FIGHEIGHT
        label = position[2]
        
        if label in dataset['code'].values:
            percent_value = dataset[dataset['code'] == label]['percent'].values[0]
            ax.scatter(x, y, color='red', s=2000, zorder=2)
            ax.text(x, y+6, f'{percent_value}%', color='red', ha='center', va='center', fontsize=12, weight="bold")
        else:
            ax.scatter(x, y, color='red', s=2000, zorder=2)
        
        #ax.text(x, y, str(i), color='white', ha='center', va='center', fontsize=12)
        ax.text(x, y, label, color='white', ha='center', va='center', fontsize=12)

FIGWIDTH = 7
FIGHEIGHT = 8
NROWS = 1
NCOLS = 1
SPACE = 0
MAX_GRID = 1

PAD_TOP = 2
PAD_BOTTOM = 2
PAD_SIDES = ((120 + PAD_TOP + PAD_BOTTOM) * FIGWIDTH / FIGHEIGHT - 80) / 2
pitch = VerticalPitch(pitch_type="wyscout",
              pad_top=PAD_TOP, pad_bottom=PAD_BOTTOM,
              pad_left=PAD_SIDES, pad_right=PAD_SIDES,
              pitch_color='white', stripe=False, line_color='gray')

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
LINHA_DEFESAS_Y = 3
LINHA_MDC_Y = 5
LINHA_MC_Y = 7
LINHA_MO_Y = LINHA_EXTREMOS_Y = 9
LINHA_PL_Y = 11

LEFT_LINE = 2
MID_LINE = 7.2
RIGHT_LINE = MID_LINE + (MID_LINE - LEFT_LINE)

team_positions = [
                                                        (MID_LINE, LINHA_GR, 'GK'),                                                       # Posicao GR
    (RIGHT_LINE, LINHA_DEFESAS_Y, 'RB'),                (MID_LINE, LINHA_DEFESAS_Y, 'CB'),           (LEFT_LINE, LINHA_DEFESAS_Y, 'LB'),  # Posicao Defesas
                                                        (MID_LINE, LINHA_MDC_Y, 'DMF'),                                                   # Posicao MDC
                                                        (MID_LINE, LINHA_MC_Y, 'CMF'),                                                    # Posicao MC
                                                        (MID_LINE, LINHA_MO_Y, 'AMF'),                                                    # Posicao MO
                                                                                                (LEFT_LINE, LINHA_EXTREMOS_Y, 'LW'),      # Posicao EE
                                                        (MID_LINE, LINHA_PL_Y, 'CF'),                                                     # Posicao PL
    (RIGHT_LINE, LINHA_EXTREMOS_Y, 'RW')                                                                                                  # Posicao ED
]

import pandas as pd

#Dados de teste
#data = {'code': ['GK', 'RB'],
#        'percent': [40, 50]}

#dataset = pd.DataFrame(data)

write_text_on_labels_from_powerbi(team_positions, dataset, ax)

plt.show()
