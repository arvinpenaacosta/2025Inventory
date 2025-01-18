
        class CircleCanvas {
            constructor(containerId, instances) {
                this.CANVAS_WIDTH = 800;
                this.CANVAS_HEIGHT = 600;
                this.instances = instances;
                this.mouseX = 0;
                this.mouseY = 0;
                this.isMouseOnCanvas = false;
                
                this.container = document.getElementById(containerId);
                this.setupDOM();
                this.setupCanvas();
                this.addEventListeners();
                
                this.resizeCanvas();
            }

            setupDOM() {
                this.coordsDisplay = document.createElement('div');
                this.coordsDisplay.style.fontFamily = 'monospace';
                this.coordsDisplay.style.margin = '10px 0';
                this.coordsDisplay.style.padding = '5px 10px';
                this.coordsDisplay.style.background = '#333';
                this.coordsDisplay.style.color = 'white';
                this.coordsDisplay.style.borderRadius = '4px';
                this.coordsDisplay.textContent = 'Pixels: X: 0, Y: 0 | Percent: X: 0%, Y: 0%';

                this.canvasContainer = document.createElement('div');
                this.canvasContainer.style.width = '100%';
                this.canvasContainer.style.display = 'flex';
                this.canvasContainer.style.justifyContent = 'center';

                this.canvas = document.createElement('canvas');
                this.canvas.style.border = '1px solid #ddd';
                this.canvas.style.maxWidth = '100%';

                this.canvasContainer.appendChild(this.canvas);
                this.container.appendChild(this.coordsDisplay);
                this.container.appendChild(this.canvasContainer);
            }

            setupCanvas() {
                this.ctx = this.canvas.getContext('2d');
            }

            resizeCanvas() {
                const containerWidth = this.canvasContainer.clientWidth;
                let newWidth = Math.min(containerWidth - 40, this.CANVAS_WIDTH);
                let newHeight = (newWidth * this.CANVAS_HEIGHT) / this.CANVAS_WIDTH;
                
                this.canvas.style.width = `${newWidth}px`;
                this.canvas.style.height = `${newHeight}px`;
                this.canvas.width = newWidth;
                this.canvas.height = newHeight;
                
                this.drawCanvas();
            }

            drawCircle(x, y, locNumber, locStation, fillColor, strokeColor) {
                const scale = this.canvas.width / this.CANVAS_WIDTH;
                const radius = 14 * scale;
                const fontSize = 18 * scale;
                const supFontSize = 12 * scale;
                const supOffset = 23 * scale;
                
                this.ctx.beginPath();
                this.ctx.arc(x, y, radius, 0, Math.PI * 2);
                this.ctx.fillStyle = fillColor;
                this.ctx.fill();
                this.ctx.strokeStyle = strokeColor;
                this.ctx.lineWidth = 2 * scale;
                this.ctx.stroke();
                
                this.ctx.fillStyle = 'black';
                this.ctx.font = `${fontSize}px Arial`;
                this.ctx.textAlign = 'center';
                this.ctx.textBaseline = 'middle';
                this.ctx.fillText(locNumber.toString(), x, y + (3 * scale));
                
                this.ctx.fillStyle = 'red';
                this.ctx.font = `${supFontSize}px Arial`;
                this.ctx.fillText(locStation.toString(), x + supOffset, y - (10 * scale));
            }

            drawCanvas() {
                this.ctx.fillStyle = '#f5f5f5';
                this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
                
                this.instances.forEach(instance => {
                    const x = instance.xPercent * this.canvas.width;
                    const y = instance.yPercent * this.canvas.height;
                    this.drawCircle(x, y, instance.locNumber, instance.locStation, 
                                instance.fillColor, instance.strokeColor);
                });

                this.drawCrosshair();
            }

            drawCrosshair() {
                if (!this.isMouseOnCanvas) return;

                this.ctx.beginPath();
                this.ctx.moveTo(0, this.mouseY);
                this.ctx.lineTo(this.canvas.width, this.mouseY);
                this.ctx.strokeStyle = 'rgba(255, 0, 0, 0.5)';
                this.ctx.lineWidth = 1;
                this.ctx.stroke();

                this.ctx.beginPath();
                this.ctx.moveTo(this.mouseX, 0);
                this.ctx.lineTo(this.mouseX, this.canvas.height);
                this.ctx.stroke();
            }

            addEventListeners() {
                this.canvas.addEventListener('mousemove', (event) => {
                    const rect = this.canvas.getBoundingClientRect();
                    this.mouseX = Math.round(event.clientX - rect.left);
                    this.mouseY = Math.round(event.clientY - rect.top);
                    
                    const xPercent = (this.mouseX / this.canvas.width * 100).toFixed(1);
                    const yPercent = (this.mouseY / this.canvas.height * 100).toFixed(1);
                    
                    this.coordsDisplay.textContent = 
                        `Pixels: X: ${this.mouseX}, Y: ${this.mouseY} | ` +
                        `Percent: X: ${(xPercent / 100).toFixed(3)}, Y: ${(yPercent / 100).toFixed(3)}`;
                    this.drawCanvas();
                });

                this.canvas.addEventListener('mouseenter', () => {
                    this.isMouseOnCanvas = true;
                });

                this.canvas.addEventListener('mouseleave', () => {
                    this.isMouseOnCanvas = false;
                    this.coordsDisplay.textContent = 'Pixels: X: 0, Y: 0 | Percent: X: 0%, Y: 0%';
                    this.drawCanvas();
                });

                window.addEventListener('resize', () => this.resizeCanvas());
            }
        }

        // Initialize the page
        document.addEventListener('DOMContentLoaded', () => {
            const statusDiv = document.getElementById('status');
            const renderButton = document.getElementById('renderButton');
            let circleCanvas = null;

            renderButton.addEventListener('click', async () => {
                try {
                    statusDiv.textContent = 'Loading locations...';
                    statusDiv.className = 'status';
                    
                    const response = await fetch('/api/locations');
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    
                    // Clear previous canvas if it exists
                    const container = document.getElementById('circleCanvas');
                    container.innerHTML = '';
                    
                    // Create new canvas with fetched data
                    circleCanvas = new CircleCanvas('circleCanvas', data.instances);
                    
                    statusDiv.textContent = 'Locations rendered successfully!';
                    statusDiv.className = 'status success';
                } catch (error) {
                    console.error('Error loading the locations:', error);
                    statusDiv.textContent = `Error: ${error.message}`;
                    statusDiv.className = 'status error';
                }
            });
        });
