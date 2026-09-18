<script>
  import { createEventDispatcher, onMount } from 'svelte';
  const dispatch = createEventDispatcher();
  
  let mode = 'login';
  let username = '';
  let password = '';
  let email = '';
  let skill_level = 'Beginner';
  let loading = false;
  let showPassword = false;
  
  let savedUsernames = [];
  let usernameSuggestions = [];
  let showUsernameSuggestions = false;

  onMount(() => {
    try {
      const stored = localStorage.getItem('ombak_saved_usernames');
      if (stored) {
        let parsed = JSON.parse(stored);
        // Handle backwards compatibility for users who have strings instead of objects
        savedUsernames = parsed.map(item => typeof item === 'string' ? {username: item, profile_pic_url: null} : item);
      }
    } catch (e) {}
  });

  function saveUsername(userObj) {
    if (!userObj || !userObj.username) return;
    
    // Remove if already exists so we can update it with the latest picture
    savedUsernames = savedUsernames.filter(u => u.username !== userObj.username);
    
    savedUsernames.push({
      username: userObj.username,
      profile_pic_url: userObj.profile_pic_url || null
    });
    
    localStorage.setItem('ombak_saved_usernames', JSON.stringify(savedUsernames));
  }

  function handleUsernameInput(e) {
    username = e.target.value;
    
    if (username.trim().length < 1) {
      usernameSuggestions = [];
      showUsernameSuggestions = false;
      return;
    }
    
    // Only search from previously logged-in/signed-up usernames on this device
    usernameSuggestions = savedUsernames
      .filter(u => u.username.toLowerCase().includes(username.toLowerCase()));
      
    showUsernameSuggestions = usernameSuggestions.length > 0;
  }
  
  function selectUsername(user) {
    username = user.username;
    usernameSuggestions = [];
    showUsernameSuggestions = false;
  }
  
  async function handleLogin() {
    if (!username || !password) return alert('Enter username & password');
    loading = true;
    try {
      const res = await fetch('/api/surf/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ username, password })
      });
      if (!res.ok) throw new Error('Invalid credentials');
      const data = await res.json();
      saveUsername(data);
      dispatch('auth', data);
    } catch (e) {
      alert(e.message);
    } finally {
      loading = false;
    }
  }

  async function handleSignup() {
    if (!username || !password || !email) return alert('Enter username, email & password');
    loading = true;
    try {
      const res = await fetch('/api/surf/users', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ username, email, password, skill_level })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Registration failed');
      
      saveUsername(data);
      dispatch('auth', data);
    } catch (e) {
      alert(e.message);
    } finally {
      loading = false;
    }
  }

  function useGuest() {
    dispatch('guest');
  }
</script>

<!-- Full-screen Deep Ocean login matching the app's sidebar aesthetic perfectly -->
<div class="min-h-screen flex items-center justify-center relative overflow-hidden bg-deep">

  <!-- Background decorative ocean waves (subtle) -->
  <div class="absolute inset-0 overflow-hidden pointer-events-none">
    <div class="absolute -bottom-32 -left-32 w-[600px] h-[600px] rounded-full bg-wave/20 blur-[100px]"></div>
    <div class="absolute top-1/4 right-0 w-[400px] h-[400px] rounded-full bg-[#1A4555]/40 blur-[80px]"></div>
    <div class="absolute bottom-1/4 right-1/4 w-[250px] h-[250px] rounded-full bg-coral/10 blur-[60px]"></div>
  </div>

  <!-- Center Card Container -->
  <div class="relative w-full max-w-md mx-4 animate-fade-up">

    <!-- Logo exactly matching App.svelte sidebar but larger -->
    <div class="flex flex-col items-center gap-4 mb-8">
      <div class="flex items-center gap-4">
        <svg class="w-14 h-14 text-white drop-shadow-md" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M 10 65 C 10 65, 30 20, 60 20 C 80 20, 90 40, 80 55 C 70 70, 50 60, 50 45 C 50 35, 65 30, 70 40" stroke="currentColor" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M 5 85 Q 30 65 60 85 T 95 70" stroke="currentColor" stroke-width="8" stroke-linecap="round"/>
        </svg>
        <h1 class="text-3xl font-bold leading-tight text-white tracking-wide">
          Ombak<br>Nusantara
        </h1>
      </div>
      <p class="text-white/50 tracking-widest uppercase text-xs font-bold mt-1">Surf Intelligence Platform</p>
    </div>

    <!-- Form Glass Card -->
    <div class="bg-white/[0.04] backdrop-blur-xl border border-white/10 rounded-[2rem] p-8 shadow-2xl shadow-black/40">

      <!-- Tab switcher -->
      <div class="flex bg-black/20 rounded-xl p-1.5 mb-7 border border-white/5">
        <button
          class="flex-1 py-2.5 rounded-lg text-sm font-bold transition-all duration-300 {mode === 'login' ? 'bg-wave text-white shadow-lg shadow-wave/30' : 'text-white/40 hover:text-white/80'}"
          on:click={() => mode = 'login'}>
          Log In
        </button>
        <button
          class="flex-1 py-2.5 rounded-lg text-sm font-bold transition-all duration-300 {mode === 'signup' ? 'bg-wave text-white shadow-lg shadow-wave/30' : 'text-white/40 hover:text-white/80'}"
          on:click={() => mode = 'signup'}>
          Sign Up
        </button>
      </div>

      {#if mode === 'login'}
        <div class="space-y-4">
          <!-- Username with autocomplete -->
          <div class="space-y-1.5 relative">
            <label class="text-[11px] font-bold text-white/50 uppercase tracking-widest ml-1" for="login-username">Username</label>
            <div class="relative">
              <input id="login-username" type="text" value={username} on:input={handleUsernameInput}
                class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-white text-sm font-medium placeholder:text-white/20 focus:outline-none focus:border-wave/60 focus:bg-white/10 transition-all shadow-inner"
                placeholder="Enter your username..."
                on:keydown={(e) => e.key === 'Enter' && handleLogin()}
                on:focus={() => {if(usernameSuggestions.length) showUsernameSuggestions = true;}}>
              <div class="absolute right-4 top-1/2 -translate-y-1/2 opacity-40">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
              </div>
            </div>
            {#if showUsernameSuggestions && mode === 'login'}
              <ul class="absolute z-50 w-full bg-[#133038] border border-white/10 rounded-xl mt-1 max-h-48 overflow-y-auto shadow-2xl text-left">
                {#each usernameSuggestions as suggestion}
                  <li>
                    <button class="w-full text-left px-4 py-3 text-sm text-white/80 hover:bg-white/10 hover:text-white transition-colors flex items-center gap-3" on:click={() => selectUsername(suggestion)}>
                      {#if suggestion.profile_pic_url}
                        <img src={suggestion.profile_pic_url} alt="" class="w-8 h-8 rounded-full object-cover border-2 border-wave/30">
                      {:else}
                        <div class="w-8 h-8 rounded-full bg-wave text-white font-bold flex items-center justify-center text-xs">{(suggestion.username || '?').charAt(0).toUpperCase()}</div>
                      {/if}
                      <span class="font-semibold">{suggestion.username}</span>
                    </button>
                  </li>
                {/each}
              </ul>
            {/if}
          </div>

          <!-- Password -->
          <div class="space-y-1.5">
            <label class="text-[11px] font-bold text-white/50 uppercase tracking-widest ml-1" for="login-password">Password</label>
            <div class="relative">
              {#if showPassword}
                <input id="login-password" type="text" bind:value={password} class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 pr-11 text-white text-sm font-medium placeholder:text-white/20 focus:outline-none focus:border-wave/60 focus:bg-white/10 transition-all shadow-inner" placeholder="Enter password..." on:keydown={(e) => e.key === 'Enter' && handleLogin()}>
              {:else}
                <input id="login-password" type="password" bind:value={password} class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 pr-11 text-white text-sm font-medium placeholder:text-white/20 focus:outline-none focus:border-wave/60 focus:bg-white/10 transition-all shadow-inner" placeholder="Enter password..." on:keydown={(e) => e.key === 'Enter' && handleLogin()}>
              {/if}
              <button class="absolute right-4 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/80 transition-colors" on:click={() => showPassword = !showPassword}>
                {#if showPassword}
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                {:else}
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" /></svg>
                {/if}
              </button>
            </div>
          </div>

          <button class="w-full py-4 mt-2 bg-wave hover:bg-waveLight text-white font-bold rounded-xl transition-all shadow-[0_0_20px_rgba(30,195,179,0.3)] hover:shadow-[0_0_25px_rgba(30,195,179,0.5)] hover:-translate-y-0.5 text-sm uppercase tracking-wider flex items-center justify-center gap-2" on:click={handleLogin} disabled={loading}>
            {loading ? 'Logging in...' : 'Log In'}
            {#if !loading}<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>{/if}
          </button>
        </div>

      {:else}
        <div class="space-y-4">
          <div class="space-y-1.5">
            <label class="text-[11px] font-bold text-white/50 uppercase tracking-widest ml-1" for="signup-username">Username</label>
            <input id="signup-username" type="text" bind:value={username} class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-white text-sm font-medium placeholder:text-white/20 focus:outline-none focus:border-wave/60 focus:bg-white/10 transition-all shadow-inner" placeholder="Choose a username..." on:keydown={(e) => e.key === 'Enter' && handleSignup()}>
          </div>
          <div class="space-y-1.5">
            <label class="text-[11px] font-bold text-white/50 uppercase tracking-widest ml-1" for="signup-email">Email</label>
            <input id="signup-email" type="email" bind:value={email} class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-white text-sm font-medium placeholder:text-white/20 focus:outline-none focus:border-wave/60 focus:bg-white/10 transition-all shadow-inner" placeholder="Enter your email..." on:keydown={(e) => e.key === 'Enter' && handleSignup()}>
          </div>
          <div class="space-y-1.5">
            <label class="text-[11px] font-bold text-white/50 uppercase tracking-widest ml-1" for="signup-password">Password</label>
            <div class="relative">
              {#if showPassword}
                <input id="signup-password" type="text" bind:value={password} class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 pr-11 text-white text-sm font-medium placeholder:text-white/20 focus:outline-none focus:border-wave/60 focus:bg-white/10 transition-all shadow-inner" placeholder="Create a password..." on:keydown={(e) => e.key === 'Enter' && handleSignup()}>
              {:else}
                <input id="signup-password" type="password" bind:value={password} class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 pr-11 text-white text-sm font-medium placeholder:text-white/20 focus:outline-none focus:border-wave/60 focus:bg-white/10 transition-all shadow-inner" placeholder="Create a password..." on:keydown={(e) => e.key === 'Enter' && handleSignup()}>
              {/if}
              <button class="absolute right-4 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/80 transition-colors" on:click={() => showPassword = !showPassword}>
                {#if showPassword}
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                {:else}
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" /></svg>
                {/if}
              </button>
            </div>
          </div>
          <div class="space-y-1.5">
            <label class="text-[11px] font-bold text-white/50 uppercase tracking-widest ml-1" for="signup-skill">Skill Level</label>
            <select id="signup-skill" bind:value={skill_level} class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-white text-sm font-medium focus:outline-none focus:border-wave/60 focus:bg-white/10 transition-all shadow-inner" on:keydown={(e) => e.key === 'Enter' && handleSignup()}>
              <option value="Beginner" class="bg-deep text-white">Beginner</option>
              <option value="Intermediate" class="bg-deep text-white">Intermediate</option>
              <option value="Advanced" class="bg-deep text-white">Advanced</option>
              <option value="Expert" class="bg-deep text-white">Expert</option>
            </select>
          </div>
          <button class="w-full py-4 mt-2 bg-wave hover:bg-waveLight text-white font-bold rounded-xl transition-all shadow-[0_0_20px_rgba(30,195,179,0.3)] hover:shadow-[0_0_25px_rgba(30,195,179,0.5)] hover:-translate-y-0.5 text-sm uppercase tracking-wider flex items-center justify-center gap-2" on:click={handleSignup} disabled={loading}>
            {loading ? 'Signing up...' : 'Create Account'}
            {#if !loading}<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>{/if}
          </button>
        </div>
      {/if}

      <!-- Divider -->
      <div class="flex items-center gap-4 my-6">
        <div class="h-px bg-white/10 flex-1"></div>
        <span class="text-[10px] text-white/30 font-bold uppercase tracking-widest">or</span>
        <div class="h-px bg-white/10 flex-1"></div>
      </div>

      <!-- Guest button -->
      <button class="w-full py-3.5 bg-transparent hover:bg-white/5 border-2 border-white/10 text-white/60 hover:text-white font-bold rounded-xl transition-all text-sm flex items-center justify-center gap-2" on:click={useGuest}>
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
        Continue as Guest
      </button>
    </div>

    <!-- Footer -->
    <p class="text-center text-white/30 text-[10px] font-bold uppercase tracking-widest mt-8">
      Ombak Nusantara · Surf Intelligence Platform
    </p>
  </div>
</div>

