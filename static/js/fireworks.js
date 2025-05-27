class Particle {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.velocity = {
            x: (Math.random() - 0.5) * 4, // Reduced velocity for smaller effect
            y: (Math.random() - 0.5) * 4
        };
        this.alpha = 1;
        this.friction = 0.98;
        this.decay = 0.96;
    }

    draw(ctx) {
        ctx.save();
        ctx.globalAlpha = this.alpha;
        ctx.fillStyle = '#3b82f6'; // Tailwind primary-500 blue color
        ctx.beginPath();
        ctx.arc(this.x, this.y, 1.5, 0, Math.PI * 2); // Small particles
        ctx.fill();
        ctx.restore();
    }

    update(ctx) {
        this.velocity.x *= this.friction;
        this.velocity.y *= this.friction;
        this.x += this.velocity.x;
        this.y += this.velocity.y;
        this.alpha *= this.decay;
        this.draw(ctx);
    }
}

class Firework {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    createParticles(x, y) {
        const particleCount = 15; // Reduced number of particles
        for (let i = 0; i < particleCount; i++) {
            this.particles.push(new Particle(x, y));
        }
    }    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this.particles.forEach((particle, index) => {
            if (particle.alpha > 0.01) {
                particle.update(this.ctx);
            } else {
                this.particles.splice(index, 1);
            }
        });

        if (this.particles.length > 0) {
            requestAnimationFrame(() => this.animate());
        } else {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
    }

    click(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        this.createParticles(x, y);
        this.animate();
    }
}

// Initialize fireworks when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.createElement('canvas');
    canvas.id = 'fireworksCanvas';
    canvas.style.cssText = 'position: fixed; top: 0; left: 0; pointer-events: none; z-index: 9999;';
    document.body.appendChild(canvas);

    const firework = new Firework(canvas);
    document.addEventListener('click', (e) => firework.click(e));
});
