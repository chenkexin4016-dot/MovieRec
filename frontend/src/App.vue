<template>
  <div class="common-layout">
    <el-container>
      <el-header class="header">
        <div style="display: flex; align-items: center; gap: 15px;">
          <h2 @click="goHome" class="logo" title="回到首页" style="margin: 0;">🎬 智影推荐</h2>
          
          <el-select v-model="selectedAlgorithm" style="width: 160px;" size="default">
            <template #prefix>⚙️ 算法</template>
            <el-option label="深度语义 (Transformer)" value="transformer" />
            <el-option label="剧情相似 (TF-IDF)" value="content_based" />
            <el-option label="协同过滤 (Item-CF)" value="item_cf" />
            <el-option label="豆瓣霸榜 (热门)" value="popular" />
            <el-option label="随便看看 (随机)" value="random" />
          </el-select>
        </div>
        <div class="actions">
          <el-input 
            v-model="searchQuery" 
            placeholder="输入电影名或类型，回车搜索..." 
            style="width: 300px; margin-right: 20px;" 
            clearable
            @keyup.enter="handleSearch"
            @clear="goHome"
          />
          <el-dropdown @command="handleGenreSelect" style="margin-right: 10px;">
            <el-button type="primary">
              按类型推荐 ▾
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="剧情">🎭 剧情</el-dropdown-item>
                <el-dropdown-item command="喜剧">😂 喜剧</el-dropdown-item>
                <el-dropdown-item command="动作">🥊 动作</el-dropdown-item>
                <el-dropdown-item command="科幻">🛸 科幻</el-dropdown-item>
                <el-dropdown-item command="爱情">❤️ 爱情</el-dropdown-item>
                <el-dropdown-item command="动画">🧚‍♂️ 动画</el-dropdown-item>
                <el-dropdown-item command="犯罪">🔫 犯罪</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button type="success" @click="fetchRecommendations">✨ 猜你喜欢</el-button>
          <el-switch
            v-model="isDarkMode"
            inline-prompt
            style="margin-left: 20px; --el-switch-on-color: #2c2c2c; --el-switch-off-color: #f2f2f2"
            active-text="🌙"
            inactive-text="☀️"
            @change="toggleDarkMode"
          />
          
          <div class="user-section" style="margin-left: 20px; display: inline-block;">
            <span v-if="currentUser" class="greeting">
              欢迎, 
              <strong 
                @click="openProfileDrawer" 
                style="cursor: pointer; color: var(--el-color-primary); text-decoration: underline;" 
                title="查看我的足迹"
              >
                {{ currentUser }}
              </strong>
              <el-button type="danger" link @click="handleLogout" style="margin-left: 10px;">退出</el-button>
            </span>
            <el-button v-else type="primary" plain @click="showLoginDialog = true">登录 / 注册</el-button>
          </div>
        </div>
      </el-header>

      <el-main>
        <div class="emotion-section">
          <h3>今天是什么心情？</h3>
          <el-button round v-for="emotion in emotions" :key="emotion" @click="filterByEmotion(emotion)">
            {{ emotion }}
          </el-button>
        </div>

        <el-row :gutter="20" class="movie-grid">
          <el-col :span="6" v-for="movie in displayedMovies" :key="movie.id" style="margin-bottom: 20px;">
            <el-card :body-style="{ padding: '0px', cursor: 'pointer' }" shadow="hover" @click="openMovieDetail(movie)">
              <img :src="'https://image.baidu.com/search/down?url=' + movie.cover_url" class="image" />
              <div style="padding: 14px;">
                <span class="movie-title">{{ movie.title }}</span>
                <div class="tags">
                  <el-tag size="small" type="info">{{ movie.genres }}</el-tag>
                  <el-tag size="small" type="warning" style="margin-left: 5px;">{{ movie.emotion }}</el-tag>
                </div>
                <div class="bottom-info">
                  <el-rate v-model="movie.rating" disabled show-score text-color="#ff9900" />
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>

    <el-dialog v-model="showLoginDialog" title="欢迎来到电影世界" width="400px" center>
      <el-tabs v-model="activeTab" class="auth-tabs">
        
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" label-width="80px" style="margin-top: 20px;">
            <el-form-item label="用户名">
              <el-input v-model="loginForm.username" placeholder="请输入账号" />
            </el-form-item>
            <el-form-item label="密 码">
              <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" show-password @keyup.enter="handleLogin" />
            </el-form-item>
            <el-button type="primary" style="width: 100%; margin-top: 10px;" @click="handleLogin">登 录</el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form :model="registerForm" label-width="80px" style="margin-top: 20px;">
            <el-form-item label="用户名">
              <el-input v-model="registerForm.username" placeholder="设置一个炫酷的昵称" />
            </el-form-item>
            <el-form-item label="密 码">
              <el-input v-model="registerForm.password" type="password" placeholder="设置密码" show-password />
            </el-form-item>
            <el-form-item label="确认密码">
              <el-input v-model="registerForm.confirmPassword" type="password" placeholder="再次输入密码" show-password />
            </el-form-item>
            <el-button type="success" style="width: 100%; margin-top: 10px;" @click="handleRegister">注 册</el-button>
          </el-form>
        </el-tab-pane>

      </el-tabs>
    </el-dialog>

  <el-dialog v-model="showDetailDialog" :title="currentMovie.title" width="600px" destroy-on-close>
      <div style="display: flex; gap: 20px;">
        <img :src="'https://image.baidu.com/search/down?url=' + currentMovie.cover_url" style="width: 200px; border-radius: 8px;" />
        
        <div style="flex: 1;">
          <p><strong>导演：</strong>{{ currentMovie.director || '暂无信息' }}</p>
          <p><strong>主演：</strong>{{ currentMovie.cast || '暂无信息' }}</p>
          <p><strong>类型：</strong>{{ currentMovie.genres }}</p>
          <p style="color: #666; font-size: 14px; line-height: 1.6;"><strong>简介：</strong>{{ currentMovie.description }}</p>
          
          <el-divider />
          
          <div style="text-align: center; margin-top: 20px;">
            <h3>您给这部电影打几星？</h3>
            <el-rate v-model="userRating" size="large" allow-half @change="submitRating" />
          </div>
        </div>
      </div>
    </el-dialog>

    <el-drawer
      v-model="showProfileDrawer"
      title="我的光影足迹"
      size="400px"
      direction="rtl"
      destroy-on-close
    >
      <el-empty v-if="userRatingsHistory.length === 0" description="您还没有给任何电影打过分哦！">
        <el-button type="primary" @click="showProfileDrawer = false">去逛逛</el-button>
      </el-empty>

      <el-timeline v-else style="padding: 10px;">
        <el-timeline-item
          v-for="item in userRatingsHistory"
          :key="item.movie_id"
          :timestamp="item.rated_at"
          placement="top"
          type="success"
        >
          <el-card :body-style="{ padding: '10px' }" shadow="hover" style="display: flex; align-items: center; gap: 15px;">
            <img :src="'https://image.baidu.com/search/down?url=' + item.cover_url" style="width: 60px; height: 80px; object-fit: cover; border-radius: 4px;" />
            
            <div style="flex: 1;">
              <span style="font-weight: bold; font-size: 15px; display: block; margin-bottom: 5px;">{{ item.movie_title }}</span>
              <div style="display: flex; align-items: center; gap: 5px;">
                <span style="font-size: 13px; color: #999;">打分：</span>
                <el-rate v-model="item.user_score" disabled show-score text-color="#ff9900" size="small" />
              </div>
              <p style="font-size: 13px; color: #666; margin-top: 5px; line-height: 1.4; border-top: 1px solid var(--el-border-color-light); padding-top: 5px;">
                评语：{{ item.comment }}
              </p>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-drawer>

  </div>
</template>


<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus' // 引入消息提示弹窗

const searchQuery = ref('')
const emotions = ref(['治愈', '搞笑', '致郁', '热血', '烧脑', '放松'])
const displayedMovies = ref([])

// ----------------- 用户系统相关状态 -----------------
const showLoginDialog = ref(false) // 控制弹窗显示/隐藏
const activeTab = ref('login') // 控制当前是在登录页还是注册页
const currentUser = ref(localStorage.getItem('username') || '') // 从本地缓存尝试读取用户名

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', password: '', confirmPassword: '' })

// ----------------- 获取电影数据 -----------------
const fetchMovies = async (emotion = '') => {
  try {
    let url = 'http://127.0.0.1:8000/api/movies'
    if (emotion) url += `?emotion=${emotion}`
    const response = await fetch(url)
    const data = await response.json()
    displayedMovies.value = data
  } catch (error) {
    ElMessage.error("获取电影数据失败")
  }
}

onMounted(() => {
  fetchMovies()
})

const filterByEmotion = (emotion) => {
  fetchMovies(emotion)
}

// ----------------- 回到首页逻辑 -----------------
const goHome = () => {
  fetchMovies() // 重新向后端请求默认的 50 部电影列表
  searchQuery.value = '' // 顺便把搜索框清空
  ElMessage.success('已回到首页')
}

// 当前选中的推荐算法，默认使用剧情相似 (TF-IDF)
const selectedAlgorithm = ref('content_based')

// ----------------- 触发个性化推荐算法 -----------------
const fetchRecommendations = async () => {
  const token = localStorage.getItem('token')
  if (!token) {
    ElMessage.warning('请先登录，系统才能根据您的口味生成专属推荐哦！')
    return
  }

  try {
    // 👇 极其关键的修改：把下拉框选中的算法变量拼接在 URL 后面 👇
    const url = `http://127.0.0.1:8000/api/recommend?algo=${selectedAlgorithm.value}`
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}` 
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      displayedMovies.value = data
      ElMessage.success('✨ 专属推荐已生成！')
    } else {
      ElMessage.error('获取推荐失败，请检查后端运行状态')
    }
  } catch (error) {
    ElMessage.error("网络请求失败")
  }
}

// ----------------- 登录逻辑 -----------------
const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码！')
    return
  }

  try {
    // ⚠️ 重点：FastAPI 的 OAuth2 接口要求前端传表单数据 (FormData) 而不是 JSON
    const formData = new URLSearchParams()
    formData.append('username', loginForm.username)
    formData.append('password', loginForm.password)

    const response = await fetch('http://127.0.0.1:8000/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    })
    
    const data = await response.json()

    if (response.ok) {
      // 登录成功：保存手环 (Token) 和用户名到浏览器缓存
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('username', loginForm.username)
      
      currentUser.value = loginForm.username // 更新页面显示
      showLoginDialog.value = false // 关闭弹窗
      ElMessage.success('登录成功，欢迎回来！')
    } else {
      ElMessage.error(data.detail || '用户名或密码错误')
    }
  } catch (error) {
    ElMessage.error("网络请求失败，请检查后端是否运行")
  }
}

// ----------------- 注册逻辑 -----------------
const handleRegister = async () => {
  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.error('两次输入的密码不一致！')
    return
  }
  if (!registerForm.username || !registerForm.password) {
    ElMessage.warning('请完整填写注册信息！')
    return
  }

  try {
    // 注册接口接收的是普通的 JSON 数据
    const response = await fetch('http://127.0.0.1:8000/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: registerForm.username,
        password: registerForm.password
      })
    })
    
    const data = await response.json()

    if (response.ok) {
      ElMessage.success('注册成功！请直接登录')
      // 注册成功后，自动把用户名填入登录框，并切换到登录面板
      loginForm.username = registerForm.username
      loginForm.password = ''
      activeTab.value = 'login' 
    } else {
      ElMessage.error(data.detail || '注册失败，可能用户名已被占用')
    }
  } catch (error) {
    ElMessage.error("网络请求失败")
  }
}

// ----------------- 退出登录 -----------------
const handleLogout = () => {
  // 摘掉手环，清空缓存
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  currentUser.value = ''
  ElMessage.info('您已退出登录')
}

// ----------------- 用户个人中心逻辑 -----------------
const showProfileDrawer = ref(false) // 控制抽屉显示
const userRatingsHistory = ref([]) // 存储从后端拿来的打分历史

const openProfileDrawer = async () => {
  // 1. 先验证手环
  const token = localStorage.getItem('token')
  if (!token) {
    ElMessage.warning('请先登录后查看个人中心')
    showLoginDialog.value = true
    return
  }

  // 2. 带着手环去向后端查数据
  try {
    const response = await fetch('http://127.0.0.1:8000/api/user/ratings', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}` 
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      userRatingsHistory.value = data // 把数据存起来
      showProfileDrawer.value = true // 打开抽屉
    } else {
      ElMessage.error('获取个人历史失败')
    }
  } catch (error) {
    ElMessage.error("网络请求失败")
  }
}

// ----------------- 搜索逻辑 -----------------
const handleSearch = async () => {
  console.log("正在搜索关键词:", searchQuery.value) // 调试信息
  
  if (!searchQuery.value) {
    fetchMovies() 
    return
  }

  try {
    // 统一使用 127.0.0.1，并加上 await 确保同步执行
    const url = `http://127.0.0.1:8000/api/movies?query=${encodeURIComponent(searchQuery.value)}`
    const response = await fetch(url)
    const data = await response.json()
    
    displayedMovies.value = data
    ElMessage.success(`为您找到 ${data.length} 部相关电影`)
  } catch (error) {
    console.error("搜索请求失败:", error)
    ElMessage.error("搜索失败，请检查后端")
  }
}

// ----------------- 按类型推荐逻辑 -----------------
const handleGenreSelect = (genre) => {
  // 1. 把用户选中的类型（比如"科幻"）自动填入搜索框
  searchQuery.value = genre 
  // 2. 直接调用我们刚才写好的搜索函数！完美代码复用！
  handleSearch() 
}

// ----------------- 暗黑模式切换逻辑 -----------------
// 尝试从本地缓存读取主题，默认是白天
const isDarkMode = ref(localStorage.getItem('theme') === 'dark')

const toggleDarkMode = (isDark) => {
  if (isDark) {
    document.documentElement.classList.add('dark') // 给网页根元素打上暗黑标记
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

// 确保页面一加载，就应用正确的模式 (这段代码可以放在你原来的 onMounted 里面)
onMounted(() => {
  fetchMovies()
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark')
  }
})

// ----------------- 电影详情与打分逻辑 (你之前漏掉的这部分！) -----------------
const showDetailDialog = ref(false)
const currentMovie = ref({})
const userRating = ref(0) // 用户给当前电影的打分

// 打开详情弹窗
const openMovieDetail = (movie) => {
  currentMovie.value = movie
  userRating.value = 0 // 每次打开清空星星
  showDetailDialog.value = true
}

// 提交打分给后端
const submitRating = async (score) => {
  const token = localStorage.getItem('token')
  if (!token) {
    ElMessage.warning('请先登录后再进行打分哦！')
    userRating.value = 0 // 把星星重置为0
    return
  }

  try {
    const response = await fetch('http://127.0.0.1:8000/api/rate', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}` // 亮出手环！
      },
      body: JSON.stringify({
        movie_id: currentMovie.value.id,
        score: score * 2 // 存入数据库通常是 10 分制，前端 5 颗星，所以乘以 2
      })
    })

    if (response.ok) {
      ElMessage.success('打分成功！您的品味将被系统铭记！')
    } else {
      ElMessage.error('打分失败，请稍后重试')
    }
  } catch (error) {
    ElMessage.error("网络请求失败")
  }
}

</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  /* 魔法在这里：把写死的颜色换成动态变量 */
  background-color: var(--el-bg-color-overlay);
  border-bottom: 1px solid var(--el-border-color-light);
  color: var(--el-text-color-primary); 
  padding: 0 20px;
}
/* 这个是包裹整个情绪区域的大盒子，负责居中 */
.emotion-section {
  margin-bottom: 30px;
  text-align: center; 
}
/* 这个是专门控制里面那个 "今天是什么心情？" 标题的颜色，适配黑夜模式 */
.emotion-section h3 {
  color: var(--el-text-color-primary);
}
/* ✅ 新样式：保持原比例缩放 */
.detail-content img {
  width: auto;      /* 宽度设为自动，让它自适应 */
  height: auto;     /* 高度设为自动 */
  max-width: 100%;  /* 限制最大宽度，不能超出容器 */
  max-height: 400px; /* 限制最大高度，比如 400px，你可以自己调整 */
  object-fit: contain; /* 🌟 魔法属性：在保持原比例的同时，缩放到最大尺寸 */
  border-radius: 8px;
  display: block;   /* 使其成为块级元素以便居中 */
  margin: 0 auto;   /* 在弹窗内居中显示 */
}
.logo {
  cursor: pointer;
  transition: opacity 0.2s;
  color: var(--el-text-color-primary); /* Logo 颜色也动态适应 */
}
.logo:hover {
  opacity: 0.8;
}
/* 加上这句，让整个网页的底层背景色也跟着变黑 */
:global(html.dark body) {
  background-color: #141414;
}
.greeting {
  font-size: 14px;
  color: #606266;
}
.movie-title {
  font-weight: bold;
  font-size: 16px;
  display: block;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis; /* 电影名字太长时显示省略号 */
}
.tags {
  margin-bottom: 10px;
}
.image {
  width: 100%;
  height: 320px;
  object-fit: cover;
  display: block;
}
.bottom-info {
  margin-top: 13px;
  line-height: 12px;
}
/* 优化弹窗内标签页的样式 */
:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
}
.logo {
  cursor: pointer;
  transition: opacity 0.2s;
}
.logo:hover {
  opacity: 0.8;
}
</style>