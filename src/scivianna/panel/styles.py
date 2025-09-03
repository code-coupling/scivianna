"""CSS style of a Card layout, removes the shaddows."""

card_style = {
    # 'border-radius': '5px',
    # 'border': '2px solid black',
    # 'padding': '20px',
    # 'margin': "10px",
    # 'background': 'White',
    "box-shadow": "0px 0px 0px #bcbcbc",
}


def customize_axis(axis, vertical=False):
    # return
    axis.visible = False

    if False:
        # No label text...
        # axis.axis_label_align =  "center"
        # axis.axis_label_orientation =  "parallel"
        # axis.axis_label_standoff =  500    #   No effect?
        # axis.axis_label_text_align =  "left"
        # axis.axis_label_text_alpha =  0.0
        # axis.axis_label_text_baseline =  "bottom"
        # axis.axis_label_text_color =  "#444444"
        # axis.axis_label_text_font =  "helvetica"
        # axis.axis_label_text_font_size =  "13px"
        # axis.axis_label_text_font_style =  "italic"
        # axis.axis_label_text_line_height =  1.2
        # axis.axis_label_text_outline_color =  None

        # Axis line
        axis.axis_line_alpha = 0.0
        # axis.axis_line_cap =  "butt"
        # axis.axis_line_color =  "gray"
        # axis.axis_line_dash =  []
        axis.axis_line_dash_offset = 0
        # axis.axis_line_join =  "bevel"
        axis.axis_line_width = 1

        # axis.background_fill_alpha =  0.0  # no effect? probably behind the label
        # axis.background_fill_color =  "red"  # no effect? probably behind the label

        #   Not used here
        # axis.background_hatch_alpha =  1.0
        # axis.background_hatch_color =  "black"
        # axis.background_hatch_pattern =  None
        # axis.background_hatch_scale =  12.0
        # axis.background_hatch_weight =  1.0

        #
        if vertical:
            axis.major_label_standoff = (
                -35
            )  #   Vertical offset -> negative means in the frame
        else:
            axis.major_label_standoff = (
                -25
            )  #   Vertical offset -> negative means in the frame
        axis.major_label_text_align = "right"
        # axis.major_label_text_alpha =  1.0 #   Set at 0 removes the labels and their background
        # axis.major_label_text_baseline =  "alphabetic"
        # axis.major_label_text_color =  "#444444"
        # axis.major_label_text_font =  "helvetica"
        # axis.major_label_text_font_size =  "11px"
        # axis.major_label_text_font_style =  "normal"
        # axis.major_label_text_line_height =  -50    #   No effect?
        # axis.major_label_text_outline_color =  None    #   Outline color

        axis.major_tick_in = 5
        # axis.major_tick_line_alpha =  1.0
        # axis.major_tick_line_cap =  "butt"
        axis.major_tick_line_color = "gray"
        # axis.major_tick_line_dash =  []
        # axis.major_tick_line_dash_offset =  0
        # axis.major_tick_line_join =  "bevel"
        # axis.major_tick_line_width =  1
        # axis.major_tick_out =  6

        axis.minor_tick_in = 3
        # axis.minor_tick_line_alpha =  1.0
        # axis.minor_tick_line_cap =  "butt"
        axis.minor_tick_line_color = "gray"
        # axis.minor_tick_line_dash =  []
        # axis.minor_tick_line_dash_offset =  0
        # axis.minor_tick_line_join =  "bevel"
        # axis.minor_tick_line_width =  1
        # axis.minor_tick_out =  4
