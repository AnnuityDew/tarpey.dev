// default layout items for Plotly.js charts
var tarpeydevLayout = {
    paper_bgcolor: 'rgba(0,0,0,1)',
    plot_bgcolor: 'rgba(255,255,255,0.2)',
    font: {
        color: '#FFFFFF',
        size: 16,
    },
    hoverlabel: {
        font: {
            color: '#FFFFFF',
        },
        bgcolor: '#555555',
    },
    title: {x:0.05},
    xaxis: {
        gridcolor: '#555555',
        showgrid: true,
        showline: true,
    },
    yaxis: {
        gridcolor: '#555555',
        showgrid: true,
        showline: true,
    },
};

var tarpeydevDefault = Plotly.makeTemplate({
    layout: tarpeydevLayout,
});