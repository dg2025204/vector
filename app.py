import streamlit as st
import streamlit.components.v1 as components

# 페이지 기본 설정
st.set_page_config(page_title="Boids 군집 시뮬레이션", layout="wide")

st.title("🕊️ 2차원 벡터 기반 Boids 군집 시뮬레이션")
st.caption("수학적 벡터 연산과 3가지 조향 규칙(Separation, Alignment, Cohesion)을 실시간으로 조절해 보세요.")

# 사이드바: 실시간 변수 조절 슬라이더
st.sidebar.header("⚙️ 시뮬레이션 변수 설정")

num_boids = st.sidebar.slider("개체 수 (Boids Count)", min_value=10, max_value=150, value=60, step=5)

st.sidebar.subheader("🎯 3가지 조향 규칙 가중치")
sep_weight = st.sidebar.slider("1. 분리 (Separation) 가중치", min_value=0.0, max_value=5.0, value=1.5, step=0.1)
ali_weight = st.sidebar.slider("2. 정렬 (Alignment) 가중치", min_value=0.0, max_value=5.0, value=1.0, step=0.1)
coh_weight = st.sidebar.slider("3. 응집 (Cohesion) 가중치", min_value=0.0, max_value=5.0, value=1.0, step=0.1)

st.sidebar.subheader("🔍 인지 거리 (Perception Radius)")
sep_radius = st.sidebar.slider("분리 인지 거리", min_value=10, max_value=100, value=25)
ali_radius = st.sidebar.slider("정렬 인지 거리", min_value=10, max_value=150, value=50)
coh_radius = st.sidebar.slider("응집 인지 거리", min_value=10, max_value=150, value=50)

# HTML5 Canvas 기반 JavaScript 실시간 시뮬레이션 엔진
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ margin: 0; background-color: #1e1e24; display: flex; justify-content: center; align-items: center; }}
        canvas {{ border: 1px solid #444; border-radius: 8px; background-color: #18181c; }}
    </style>
</head>
<body>
    <canvas id="boidCanvas" width="800" height="500"></canvas>

    <script>
        const canvas = document.getElementById('boidCanvas');
        const ctx = canvas.getContext('2d');

        // Streamlit 슬라이더 파라미터 적용
        const NUM_BOIDS = {num_boids};
        const SEP_WEIGHT = {sep_weight};
        const ALI_WEIGHT = {ali_weight};
        const COH_WEIGHT = {coh_weight};
        const SEP_RADIUS = {sep_radius};
        const ALI_RADIUS = {ali_radius};
        const COH_RADIUS = {coh_radius};

        class Vector {{
            constructor(x, y) {{ this.x = x; this.y = y; }}
            add(v) {{ this.x += v.x; this.y += v.y; return this; }}
            sub(v) {{ this.x -= v.x; this.y -= v.y; return this; }}
            mult(n) {{ this.x *= n; this.y *= n; return this; }}
            div(n) {{ this.x /= n; this.y /= n; return this; }}
            mag() {{ return Math.sqrt(this.x * this.x + this.y * this.y); }}
            setMag(n) {{ return this.normalize().mult(n); }}
            normalize() {{ let m = this.mag(); if (m !== 0) this.div(m); return this; }}
            limit(max) {{ if (this.mag() > max) this.setMag(max); return this; }}
            dist(v) {{ return Math.sqrt((this.x - v.x)**2 + (this.y - v.y)**2); }}
            static sub(v1, v2) {{ return new Vector(v1.x - v2.x, v1.y - v2.y); }}
        }}

        class Boid {{
            constructor(x, y) {{
                this.position = new Vector(x, y);
                this.velocity = new Vector((Math.random()-0.5)*4, (Math.random()-0.5)*4);
                this.acceleration = new Vector(0, 0);
                this.maxSpeed = 3.5;
                this.maxForce = 0.1;
            }}

            update() {{
                this.velocity.add(this.acceleration);
                this.velocity.limit(this.maxSpeed);
                this.position.add(this.velocity);
                this.acceleration.mult(0);

                if (this.position.x > canvas.width) this.position.x = 0;
                if (this.position.x < 0) this.position.x = canvas.width;
                if (this.position.y > canvas.height) this.position.y = 0;
                if (this.position.y < 0) this.position.y = canvas.height;
            }}

            applyForce(force) {{
                this.acceleration.add(force);
            }}

            separate(boids) {{
                let steering = new Vector(0, 0);
                let total = 0;
                for (let other of boids) {{
                    let d = this.position.dist(other.position);
                    if (other !== this && d < SEP_RADIUS) {{
                        let diff = Vector.sub(this.position, other.position);
                        if (d > 0) diff.div(d);
                        steering.add(diff);
                        total++;
                    }}
                }}
                if (total > 0) {{
                    steering.div(total);
                    if (steering.mag() > 0) steering.setMag(this.maxSpeed);
                    steering.sub(this.velocity);
                    steering.limit(this.maxForce);
                }}
                return steering;
            }}

            align(boids) {{
                let steering = new Vector(0, 0);
                let total = 0;
                for (let other of boids) {{
                    let d = this.position.dist(other.position);
                    if (other !== this && d < ALI_RADIUS) {{
                        steering.add(other.velocity);
                        total++;
                    }}
                }}
                if (total > 0) {{
                    steering.div(total);
                    steering.setMag(this.maxSpeed);
                    steering.sub(this.velocity);
                    steering.limit(this.maxForce);
                }}
                return steering;
            }}

            cohere(boids) {{
                let steering = new Vector(0, 0);
                let total = 0;
                for (let other of boids) {{
                    let d = this.position.dist(other.position);
                    if (other !== this && d < COH_RADIUS) {{
                        steering.add(other.position);
                        total++;
                    }}
                }}
                if (total > 0) {{
                    steering.div(total);
                    let desired = Vector.sub(steering, this.position);
                    desired.setMag(this.maxSpeed);
                    steering = Vector.sub(desired, this.velocity);
                    steering.limit(this.maxForce);
                }}
                return steering;
            }}

            flock(boids) {{
                let sep = this.separate(boids).mult(SEP_WEIGHT);
                let ali = this.align(boids).mult(ALI_WEIGHT);
                let coh = this.cohere(boids).mult(COH_WEIGHT);

                this.applyForce(sep);
                this.applyForce(ali);
                this.applyForce(coh);
            }}

            draw() {{
                let angle = Math.atan2(this.velocity.y, this.velocity.x);
                ctx.save();
                ctx.translate(this.position.x, this.position.y);
                ctx.rotate(angle);
                ctx.fillStyle = "#ffffff";
                ctx.beginPath();
                ctx.moveTo(8, 0);
                ctx.lineTo(-6, -4);
                ctx.lineTo(-6, 4);
                ctx.closePath();
                ctx.fill();
                ctx.restore();
            }}
        }}

        const flock = [];
        for (let i = 0; i < NUM_BOIDS; i++) {{
            flock.push(new Boid(Math.random() * canvas.width, Math.random() * canvas.height));
        }}

        function animate() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            for (let boid of flock) {{
                boid.flock(flock);
                boid.update();
                boid.draw();
            }}
            requestAnimationFrame(animate);
        }}

        animate();
    </script>
</body>
</html>
"""

# 화면에 시뮬레이션 표시
components.html(html_code, height=520)

st.markdown("""
---
### 💡 실시간 조작 가이드
* **분리 가중치를 높이면:** 서로 간격을 넓게 유지하려고 하여 무리가 넓게 퍼집니다.
* **정렬 가중치를 높이면:** 모두 같은 방향으로 나란히 깔끔하게 이동합니다.
* **응집 가중치를 높이면:** 하나의 단단한 덩어리처럼 중심부로 밀집됩니다.
""")
