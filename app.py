import streamlit as st
import streamlit.components.v1 as components

# 페이지 기본 설정
st.set_page_config(page_title="Boids 군집 시뮬레이션", layout="wide")

st.title("🕊️ 2차원 벡터 기반 Boids 군집 시뮬레이션")
st.caption("수학적 벡터 연산과 3가지 조향 규칙(Separation, Alignment, Cohesion)을 실시간으로 조절해 보세요.")

# -----------------------------------------------------------------------------
# 📖 1. 알고리즘 및 파라미터 상세 설명 섹션 (탭 & Expander 구성)
# -----------------------------------------------------------------------------
with st.expander("📚 Boids 알고리즘 및 시뮬레이션 변수 원리 알아보기", expanded=True):
    st.markdown("""
    **Boids 알고리즘**은 1986년 크레이그 레이놀즈(Craig Reynolds)가 개발한 새나 물고기 무리의 **군집 행동(Flocking Behavior)** 복잡계 시뮬레이션 모델입니다.  
    각 개체는 전체 무리의 지휘자 없이, **오직 주변 인지 거리 내의 이웃 개체들**만을 고려하여 3가지 단순한 규칙을 따릅니다.
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("1. 분리 (Separation)")
        st.markdown("""
        - **원리:** 너무 가까운 이웃 개체와 충돌하지 않도록 **반대 방향**으로 떨어집니다.
        - **분리 가중치:** 높일수록 개체 간 최소 간격 유지를 최우선시하여 무리가 넓게 퍼집니다.
        - **분리 인지 거리:** 충돌 위험을 감지하는 **개인 공간(Personal Space)** 범위를 설정합니다.
        """)
        
    with col2:
        st.subheader("2. 정렬 (Alignment)")
        st.markdown("""
        - **원리:** 주변 이웃 개체들의 **평균 이동 방향(속도 벡터)**과 내 방향을 맞춥니다.
        - **정렬 가중치:** 높일수록 일정한 방향으로 일제히 질서정연하게 이동하는 경향이 강해집니다.
        - **정렬 인지 거리:** 이동 방향을 참고할 이웃 개체들을 탐색하는 범위입니다.
        """)
        
    with col3:
        st.subheader("3. 응집 (Cohesion)")
        st.markdown("""
        - **원리:** 주변 이웃 개체들의 **평균 위치(질량 중심)**를 향해 이동합니다.
        - **응집 가중치:** 높일수록 개체들이 모여 하나의 단단한 덩어리처럼 행동합니다.
        - **응집 인지 거리:** 무리의 중심 위치 계산에 포함할 이웃 범위를 설정합니다.
        """)

    st.info("💡 **조향 힘(Steering Force) 공식:** $\\text{Steering} = \\text{Desired Velocity} - \\text{Current Velocity}$ (목표 속도에서 현재 속도를 뺀 힘을 가속도로 적용합니다.)")

st.divider()

# -----------------------------------------------------------------------------
# ⚙️ 2. 사이드바: 실시간 변수 조절 슬라이더
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ 시뮬레이션 변수 설정")

num_boids = st.sidebar.slider("개체 수 (Boids Count)", min_value=10, max_value=150, value=60, step=5)

st.sidebar.subheader("🎯 3가지 조향 규칙 가중치")
sep_weight = st.sidebar.slider("1. 분리 (Separation) 가중치", min_value=0.0, max_value=5.0, value=1.5, step=0.1)
ali_weight = st.sidebar.slider("2. 정렬 (Alignment) 가중치", min_value=0.0, max_value=5.0, value=1.0, step=0.1)
coh_weight = st.sidebar.slider("3. 응집 (Cohesion) 가중치", min_value=0.0, max_value=5.0, value=1.0, step=0.1)

st.sidebar.subheader("🔍 인지 거리 (Perception Radius)")
sep_radius = st.sidebar.slider("분리 인지 거리 (px)", min_value=10, max_value=100, value=25)
ali_radius = st.sidebar.slider("정렬 인지 거리 (px)", min_value=10, max_value=150, value=50)
coh_radius = st.sidebar.slider("응집 인지 거리 (px)", min_value=10, max_value=150, value=50)

# -----------------------------------------------------------------------------
# 🖥️ 3. HTML5 Canvas 기반 JavaScript 실시간 시뮬레이션 엔진
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 🧪 4. 실험 추천 시나리오 안내
# -----------------------------------------------------------------------------
st.markdown("""
### 🧪 추천 실험 시나리오
- **격리된 수족관 (Fish Tank):** `응집 = 3.0`, `정렬 = 0.5`, `분리 = 1.0`  
  -> 개체들이 한 덩어리로 뭉쳐 원을 그리듯 소용돌이칩니다.
- **질서정연한 철새 무리 (Migrating Birds):** `정렬 = 3.0`, `분리 = 1.5`, `응집 = 0.5`  
  -> 개체들이 깔끔하게 한 방향으로 줄지어 이동합니다.
- **분산된 모기 떼 (Swarm of Insects):** `분리 = 4.0`, `응집 = 0.0`, `정렬 = 0.0`  
  -> 서로 서로 부딪히지 않기 위해 사방으로 무질서하게 흩어집니다.
""")
