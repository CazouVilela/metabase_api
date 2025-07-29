/**
 * ChartBuilder - Constrói e gerencia o gráfico Highcharts
 * Configuração com múltiplos eixos Y
 */
class ChartBuilder {
    constructor(containerId) {
        this.containerId = containerId;
        this.chart = null;
        this.defaultOptions = this.getDefaultOptions();
    }

    /**
     * Constrói ou atualiza o gráfico
     */
    buildChart(chartData) {
        if (!chartData || chartData.series.length === 0) {
            this.showEmptyState();
            return;
        }

        this.hideEmptyState();
        
        const options = this.prepareChartOptions(chartData);
        
        if (this.chart) {
            this.chart.destroy();
        }
        
        this.chart = Highcharts.chart(this.containerId, options);
    }

    /**
     * Prepara opções do gráfico
     */
    prepareChartOptions(chartData) {
        const { categories, series } = chartData;
        
        return {
            ...this.defaultOptions,
            xAxis: {
                categories: categories,
                crosshair: true,
                labels: {
                    style: {
                        fontSize: '11px'
                    },
                    rotation: categories.length > 12 ? -45 : 0
                }
            },
            yAxis: [
                { // Eixo Y principal - Impressions
                    labels: {
                        format: '{value:,.0f}',
                        style: {
                            color: '#2E86DE'
                        }
                    },
                    title: {
                        text: 'Impressões',
                        style: {
                            color: '#2E86DE'
                        }
                    },
                    opposite: false
                },
                { // Eixo Y secundário - Clicks
                    gridLineWidth: 0,
                    title: {
                        text: 'Clicks',
                        style: {
                            color: '#FF6B6B'
                        }
                    },
                    labels: {
                        format: '{value:,.0f}',
                        style: {
                            color: '#FF6B6B'
                        }
                    },
                    opposite: true
                },
                { // Eixo Y secundário 2 - Spend
                    gridLineWidth: 0,
                    title: {
                        text: 'Investimento (R$)',
                        style: {
                            color: '#4CAF50'
                        }
                    },
                    labels: {
                        format: 'R$ {value:,.0f}',
                        style: {
                            color: '#4CAF50'
                        }
                    },
                    opposite: true,
                    offset: 80
                }
            ],
            series: series
        };
    }

    /**
     * Configurações padrão do gráfico
     */
    getDefaultOptions() {
        return {
            chart: {
                type: 'column',
                backgroundColor: 'transparent',
                style: {
                    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
                },
                animation: {
                    duration: 750
                }
            },
            title: {
                text: null
            },
            credits: {
                enabled: false
            },
            legend: {
                layout: 'horizontal',
                align: 'center',
                verticalAlign: 'bottom',
                itemStyle: {
                    fontSize: '12px'
                }
            },
            plotOptions: {
                column: {
                    stacking: 'normal',
                    borderWidth: 0,
                    dataLabels: {
                        enabled: false
                    }
                },
                spline: {
                    lineWidth: 2,
                    states: {
                        hover: {
                            lineWidth: 3
                        }
                    },
                    marker: {
                        enabled: true,
                        radius: 4
                    }
                }
            },
            tooltip: {
                shared: true,
                useHTML: true,
                headerFormat: '<div class="custom-tooltip"><b>{point.key}</b><br/>',
                pointFormat: '<span style="color:{series.color}">{series.name}:</span> ' +
                            '<b>{point.y:,.0f}</b> {series.options.tooltip.valueSuffix}<br/>',
                footerFormat: '</div>',
                backgroundColor: 'rgba(0, 0, 0, 0.85)',
                borderWidth: 0,
                shadow: true,
                style: {
                    color: '#fff',
                    fontSize: '12px'
                }
            },
            exporting: {
                enabled: true,
                buttons: {
                    contextButton: {
                        menuItems: [
                            'viewFullscreen',
                            'separator',
                            'downloadPNG',
                            'downloadJPEG',
                            'downloadSVG',
                            'separator',
                            'downloadCSV',
                            'downloadXLS'
                        ]
                    }
                }
            },
            responsive: {
                rules: [{
                    condition: {
                        maxWidth: 500
                    },
                    chartOptions: {
                        legend: {
                            layout: 'vertical',
                            align: 'center',
                            verticalAlign: 'bottom'
                        },
                        yAxis: [{
                            labels: {
                                align: 'left',
                                x: 0,
                                y: -5
                            },
                            title: {
                                text: null
                            }
                        }, {
                            labels: {
                                align: 'right',
                                x: 0,
                                y: -5
                            },
                            title: {
                                text: null
                            }
                        }, {
                            labels: {
                                align: 'right',
                                x: 0,
                                y: -5
                            },
                            title: {
                                text: null
                            },
                            offset: 40
                        }]
                    }
                }]
            }
        };
    }

    /**
     * Atualiza apenas os dados do gráfico (sem recriar)
     */
    updateData(chartData) {
        if (!this.chart) {
            this.buildChart(chartData);
            return;
        }

        const { categories, series } = chartData;

        // Atualizar categorias
        this.chart.xAxis[0].setCategories(categories, false);

        // Remover séries antigas
        while (this.chart.series.length > 0) {
            this.chart.series[0].remove(false);
        }

        // Adicionar novas séries
        series.forEach(seriesData => {
            this.chart.addSeries(seriesData, false);
        });

        // Redesenhar
        this.chart.redraw();
    }

    /**
     * Mostra estado vazio
     */
    showEmptyState() {
        const container = document.getElementById(this.containerId);
        const emptyState = document.getElementById('empty-state');
        
        if (container && emptyState) {
            emptyState.style.display = 'flex';
        }
        
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }

    /**
     * Esconde estado vazio
     */
    hideEmptyState() {
        const emptyState = document.getElementById('empty-state');
        if (emptyState) {
            emptyState.style.display = 'none';
        }
    }

    /**
     * Redimensiona o gráfico
     */
    resize() {
        if (this.chart) {
            this.chart.reflow();
        }
    }

    /**
     * Entra/sai do modo tela cheia
     */
    toggleFullscreen() {
        const container = document.querySelector('.dashboard-container');
        container.classList.toggle('fullscreen');
        
        setTimeout(() => {
            this.resize();
        }, 100);
    }

    /**
     * Exporta gráfico como imagem
     */
    exportImage(type = 'png') {
        if (this.chart) {
            this.chart.exportChart({
                type: `image/${type}`,
                filename: `grafico_performance_${new Date().toISOString().split('T')[0]}`
            });
        }
    }

    /**
     * Destrói o gráfico
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }

    /**
     * Adiciona animação de entrada
     */
    animateIn() {
        if (this.chart) {
            this.chart.series.forEach((series, index) => {
                setTimeout(() => {
                    series.setVisible(true, true);
                }, index * 100);
            });
        }
    }

    /**
     * Atualiza tema do gráfico
     */
    updateTheme(theme = 'light') {
        if (!this.chart) return;
        
        const isDark = theme === 'dark';
        
        this.chart.update({
            chart: {
                backgroundColor: isDark ? '#1a1a1a' : 'transparent'
            },
            xAxis: {
                labels: {
                    style: {
                        color: isDark ? '#ccc' : '#666'
                    }
                }
            },
            yAxis: this.chart.yAxis.map(axis => ({
                labels: {
                    style: {
                        color: isDark ? '#ccc' : axis.options.labels.style.color
                    }
                },
                title: {
                    style: {
                        color: isDark ? '#ccc' : axis.options.title.style.color
                    }
                }
            })),
            legend: {
                itemStyle: {
                    color: isDark ? '#ccc' : '#333'
                }
            }
        });
    }
}
