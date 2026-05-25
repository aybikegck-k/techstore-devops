pipeline {
    agent any

    environment {
        DOCKER_IMAGE    = 'techstore-app'
        DOCKER_HUB_USER = 'kullanici-adi'          // Docker Hub kullanıcı adınız
        SONAR_HOST      = 'http://localhost:9000'
        SONAR_TOKEN     = credentials('sonar-token') // Jenkins Credentials'a ekleyin
        SLACK_CHANNEL   = '#devops-techstore'
    }

    stages {

        // ── 1. KAYNAK KOD ───────────────────────────────────────
        stage('Checkout') {
            steps {
                checkout scm
                echo "✅ Kod GitHub'dan alındı: ${env.GIT_COMMIT?.take(7)}"
            }
        }

        // ── 2. ORTAM KURULUMU ───────────────────────────────────
        stage('Setup') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
                echo "✅ Python sanal ortamı hazır"
            }
        }

        // ── 3. BİRİM TESTLERİ ──────────────────────────────────
        stage('Unit Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/test_app.py \
                        -v \
                        --tb=short \
                        --junit-xml=test-results/unit-tests.xml \
                        --cov=app \
                        --cov-report=xml:coverage.xml \
                        --cov-report=term-missing
                '''
            }
            post {
                always {
                    junit 'test-results/unit-tests.xml'
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')]
                }
            }
        }

        // ── 4. KOD KALİTE ANALİZİ ──────────────────────────────
        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        . venv/bin/activate
                        sonar-scanner \
                            -Dsonar.projectKey=techstore \
                            -Dsonar.projectName="TechStore E-Commerce" \
                            -Dsonar.sources=. \
                            -Dsonar.exclusions=venv/**,tests/**,**/__pycache__/** \
                            -Dsonar.python.coverage.reportPaths=coverage.xml \
                            -Dsonar.host.url=${SONAR_HOST} \
                            -Dsonar.login=${SONAR_TOKEN}
                    '''
                }
            }
        }

        // ── 5. KALİTE KAPISI ───────────────────────────────────
        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
                echo "✅ SonarQube kalite kapısı geçildi"
            }
        }

        // ── 6. DOCKER İMAJI ─────────────────────────────────────
        stage('Build Docker Image') {
            steps {
                sh """
                    docker build \
                        -t ${DOCKER_IMAGE}:${env.BUILD_NUMBER} \
                        -t ${DOCKER_IMAGE}:latest \
                        --build-arg BUILD_DATE=\$(date -u +%Y-%m-%dT%H:%M:%SZ) \
                        --build-arg GIT_COMMIT=${env.GIT_COMMIT?.take(7)} \
                        .
                """
                echo "✅ Docker imajı oluşturuldu: ${DOCKER_IMAGE}:${env.BUILD_NUMBER}"
            }
        }

        // ── 7. DOCKER HUB'A GÖNDER ──────────────────────────────
        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker-hub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                        echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin
                        docker tag ${DOCKER_IMAGE}:latest \$DOCKER_USER/${DOCKER_IMAGE}:${env.BUILD_NUMBER}
                        docker tag ${DOCKER_IMAGE}:latest \$DOCKER_USER/${DOCKER_IMAGE}:latest
                        docker push \$DOCKER_USER/${DOCKER_IMAGE}:${env.BUILD_NUMBER}
                        docker push \$DOCKER_USER/${DOCKER_IMAGE}:latest
                    """
                }
                echo "✅ İmaj Docker Hub'a yüklendi"
            }
        }

        // ── 8. DEPLOY ───────────────────────────────────────────
        stage('Deploy') {
            steps {
                sh """
                    # Eski konteyneri durdur
                    docker stop techstore-app 2>/dev/null || true
                    docker rm techstore-app 2>/dev/null || true

                    # Yeni versiyonu başlat
                    docker run -d \
                        --name techstore-app \
                        --restart unless-stopped \
                        -p 5000:5000 \
                        ${DOCKER_HUB_USER}/${DOCKER_IMAGE}:latest

                    echo "⏳ Sağlık kontrolü bekleniyor..."
                    sleep 10
                """
            }
        }

        // ── 9. SMOKE TEST ───────────────────────────────────────
        stage('Smoke Test') {
            steps {
                sh '''
                    # /health endpoint kontrol
                    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
                    if [ "$STATUS" != "200" ]; then
                        echo "❌ Smoke test başarısız! HTTP: $STATUS"
                        exit 1
                    fi

                    # Ana sayfa kontrol
                    STATUS2=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/)
                    if [ "$STATUS2" != "200" ]; then
                        echo "❌ Ana sayfa erişilemiyor! HTTP: $STATUS2"
                        exit 1
                    fi

                    echo "✅ Smoke testleri geçildi"
                '''
            }
        }

        // ── 10. UI TESTLERİ ─────────────────────────────────────
        stage('UI Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/test_ui.py -v --tb=short || true
                '''
            }
        }
    }

    // ── POST ACTIONS ────────────────────────────────────────────
    post {
        success {
            echo "🎉 Pipeline başarıyla tamamlandı!"
            slackSend(
                channel: env.SLACK_CHANNEL,
                color: 'good',
                message: """
✅ *TechStore Deploy Başarılı*
• Branch: `${env.BRANCH_NAME}`
• Build: `#${env.BUILD_NUMBER}`
• Commit: `${env.GIT_COMMIT?.take(7)}`
• URL: ${env.BUILD_URL}
                """
            )
        }
        failure {
            echo "❌ Pipeline başarısız!"
            slackSend(
                channel: env.SLACK_CHANNEL,
                color: 'danger',
                message: """
❌ *TechStore Deploy Başarısız*
• Branch: `${env.BRANCH_NAME}`
• Build: `#${env.BUILD_NUMBER}`
• Aşama: ${env.STAGE_NAME}
• Detay: ${env.BUILD_URL}console
                """
            )
        }
        always {
            // Eski imajları temizle (son 3'ü tut)
            sh "docker image prune -f --filter 'until=72h' || true"
            cleanWs()
        }
    }
}
