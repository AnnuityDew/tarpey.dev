# import third party packages
import plotly.graph_objects as go


def tarpeydev_default():
    tarpeydev_template = go.layout.Template()

    # plot style defaults for the site
    tarpeydev_template.layout.autosize = True
    tarpeydev_template.layout.paper_bgcolor = 'rgba(0,0,0,1)'
    tarpeydev_template.layout.plot_bgcolor = 'rgba(255,255,255,0.2)'
    tarpeydev_template.layout.font = dict(color='#FFFFFF', size=16)
    tarpeydev_template.layout.hoverlabel.font = dict(color='#FFFFFF')
    tarpeydev_template.layout.hoverlabel = dict(bgcolor='#555555')
    tarpeydev_template.layout.title = dict(x=0.05)
    tarpeydev_template.layout.xaxis.gridcolor = '#555555'
    tarpeydev_template.layout.xaxis.showgrid = True
    tarpeydev_template.layout.xaxis.showline = True
    tarpeydev_template.layout.yaxis.gridcolor = '#555555'
    tarpeydev_template.layout.yaxis.showgrid = True
    tarpeydev_template.layout.yaxis.showline = True

    # bar data defaults for the site. colors based on
    # plotly.colors.qualitative.Prism
    tarpeydev_template.data.bar = [
        go.Bar(marker=dict(color='rgba(102, 197, 204, 0.6)', line=dict(color='rgba(102, 197, 204, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(246, 207, 113, 0.6)', line=dict(color='rgba(246, 207, 113, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(248, 156, 116, 0.6)', line=dict(color='rgba(248, 156, 116, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(220, 176, 242, 0.6)', line=dict(color='rgba(220, 176, 242, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(135, 197, 95, 0.6)', line=dict(color='rgba(135, 197, 95, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(158, 185, 243, 0.6)', line=dict(color='rgba(158, 185, 243, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(254, 136, 177, 0.6)', line=dict(color='rgba(254, 136, 177, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(201, 219, 116, 0.6)', line=dict(color='rgba(201, 219, 116, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(139, 224, 164, 0.6)', line=dict(color='rgba(139, 224, 164, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(180, 151, 231, 0.6)', line=dict(color='rgba(180, 151, 231, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(251, 180, 174, 0.6)', line=dict(color='rgba(251, 180, 174, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(179, 205, 227, 0.6)', line=dict(color='rgba(179, 205, 227, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(204, 235, 197, 0.6)', line=dict(color='rgba(204, 235, 197, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(222, 203, 228, 0.6)', line=dict(color='rgba(222, 203, 228, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(254, 217, 166, 0.6)', line=dict(color='rgba(254, 217, 166, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(255, 255, 204, 0.6)', line=dict(color='rgba(255, 255, 204, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(229, 216, 189, 0.6)', line=dict(color='rgba(229, 216, 189, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(253, 218, 236, 0.6)', line=dict(color='rgba(253, 218, 236, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(179, 226, 205, 0.6)', line=dict(color='rgba(179, 226, 205, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(253, 205, 172, 0.6)', line=dict(color='rgba(253, 205, 172, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(203, 213, 232, 0.6)', line=dict(color='rgba(203, 213, 232, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(244, 202, 228, 0.6)', line=dict(color='rgba(244, 202, 228, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(230, 245, 201, 0.6)', line=dict(color='rgba(230, 245, 201, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(255, 242, 174, 0.6)', line=dict(color='rgba(255, 242, 174, 1.0)', width=2))),
        go.Bar(marker=dict(color='rgba(241, 226, 204, 0.6)', line=dict(color='rgba(241, 226, 204, 1.0)', width=2))),
    ]

    return tarpeydev_template


def tarpeydev_black():
    tarpeydev_black = tarpeydev_default()

    tarpeydev_black.layout.paper_bgcolor = 'rgba(0,0,0,1)'
    tarpeydev_black.layout.plot_bgcolor = 'rgba(255,255,255,0)'

    return tarpeydev_black