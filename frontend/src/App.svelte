<script>
  import Auth from './Auth.svelte';
  import Dashboard from './Dashboard.svelte';
  import SurfPlanner from './SurfPlanner.svelte';
  import SocialFeed from './SocialFeed.svelte';
  import Community from './Community.svelte';
  import Hazard from './Hazard.svelte';
  import Surfing from './Surfing.svelte';
  import MyProfile from './MyProfile.svelte';
  import SurfMap from './SurfMap.svelte';
  import Toast from './components/Toast.svelte';
  import { fade, fly } from 'svelte/transition';
  
  let user = null;
  let activeTab = 'dashboard';
  let isGuest = false;
  
  function handleAuth(event) {
    user = event.detail;
    isGuest = false;
    activeTab = 'dashboard';
  }
  
  function handleGuest() {
    user = null;
    isGuest = true;
    activeTab = 'surfing';
  }
  
  function handleLogout() {
    user = null;
    isGuest = false;
    activeTab = 'dashboard';
  }
  
  let notifications = [];
  let showNotifications = false;
  
  async function fetchNotifications() {
    if (!user) return;
    try {
      const res = await fetch(`/api/social/notifications?user_id=${user.id}`);
      if (res.ok) notifications = await res.json();
    } catch (e) {}
  }
  
  let focusPostId = null;
  
  $: unreadCount = notifications.filter(n => !n.is_read).length;

  async function markAsRead(notif) {
    if (notif.is_read) return;
    try {
      await fetch(`/api/social/notifications/${notif.id}/read`, { method: 'PUT' });
      notif.is_read = true;
      notifications = [...notifications];
    } catch (e) {}
  }
  
  async function markAllAsRead() {
    try {
      await fetch(`/api/social/notifications/read-all?user_id=${user.id}`, { method: 'PUT' });
      notifications = notifications.map(n => ({...n, is_read: true}));
    } catch (e) {}
  }
  
  import { onMount } from 'svelte';
  onMount(() => {
    const intv = setInterval(() => { if (user) fetchNotifications(); }, 10000);
    return () => clearInterval(intv);
  });

  // Reactively fetch notifications whenever user changes (login)
  $: if (user) fetchNotifications();
</script>

{#if !user && !isGuest}
  <Auth on:auth={handleAuth} on:guest={handleGuest} />
{:else}
  <Toast />
  <div class="flex items-center justify-center min-h-screen bg-mesh overflow-hidden text-[#0F2922]">
    
    <!-- Fullscreen Premium Container -->
    <div class="flex w-full h-screen bg-[#F1F5F2]/80 backdrop-blur-3xl overflow-hidden relative animate-fade-up">
      
      <!-- Sidebar (Deep Ocean Blue) -->
      <aside class="w-64 bg-deep text-white/90 flex flex-col justify-between py-10 px-6 flex-shrink-0 z-20 shadow-xl">
        <div>
          <!-- Logo -->
          <div class="flex items-center gap-3 mb-12 cursor-pointer hover:opacity-80 transition-opacity">
            <svg class="w-10 h-10 text-white" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M 10 65 C 10 65, 30 20, 60 20 C 80 20, 90 40, 80 55 C 70 70, 50 60, 50 45 C 50 35, 65 30, 70 40" stroke="currentColor" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M 5 85 Q 30 65 60 85 T 95 70" stroke="currentColor" stroke-width="8" stroke-linecap="round"/>
            </svg>
            <h1 class="text-xl font-bold leading-tight text-white tracking-wide">
              Ombak<br>Nusantara
            </h1>
          </div>
          
          <!-- Navigation -->
          <nav class="space-y-1.5 font-medium text-sm">
            {#if !isGuest}
              <button class="flex items-center gap-4 w-full px-4 py-3 rounded-xl transition-all {activeTab === 'dashboard' ? 'bg-wave text-white font-bold shadow-md shadow-wave/20' : 'hover:bg-white/10 hover:text-white'}" on:click={() => activeTab = 'dashboard'}>
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path></svg>
                Dashboard
              </button>
            {/if}
            
            <button class="flex items-center gap-4 w-full px-4 py-3 rounded-xl transition-all {activeTab === 'surfing' ? 'bg-wave text-white font-bold shadow-md shadow-wave/20' : 'hover:bg-white/10 hover:text-white'}" on:click={() => activeTab = 'surfing'}>
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
              Surf Spots
            </button>
            
            {#if !isGuest}
              <button class="flex items-center gap-4 w-full px-4 py-3 rounded-xl transition-all {activeTab === 'feed' ? 'bg-wave text-white font-bold shadow-md shadow-wave/20' : 'hover:bg-white/10 hover:text-white'}" on:click={() => activeTab = 'feed'}>
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                Session
              </button>

              <button class="flex items-center gap-4 w-full px-4 py-3 rounded-xl transition-all {activeTab === 'community' ? 'bg-wave text-white font-bold shadow-md shadow-wave/20' : 'hover:bg-white/10 hover:text-white'}" on:click={() => activeTab = 'community'}>
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
                Community
              </button>
              
              <button class="flex items-center gap-4 w-full px-4 py-3 rounded-xl transition-all {activeTab === 'hazard' ? 'bg-wave text-white font-bold shadow-md shadow-wave/20' : 'hover:bg-white/10 hover:text-white'}" on:click={() => activeTab = 'hazard'}>
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                Hazard Alert
              </button>
            {/if}
          </nav>
        </div>
        
        <!-- Profile Footer -->
        {#if !isGuest}
          <div class="space-y-1.5 relative">
            <!-- Profile Button -->
            <button class="flex items-center gap-3 w-full p-2.5 hover:bg-white/10 rounded-xl transition-colors cursor-pointer text-left border border-transparent hover:border-white/10 group" on:click={() => activeTab = 'profile'}>
              {#if user.profile_pic_url}
                <img src={user.profile_pic_url} alt="Profile" class="w-10 h-10 rounded-full object-cover flex-shrink-0 border-2 border-white/20" />
              {:else}
                <div class="w-10 h-10 rounded-full bg-wave flex items-center justify-center text-white font-bold flex-shrink-0 border-2 border-white/20">
                  {user.username.charAt(0).toUpperCase()}
                </div>
              {/if}
              <div class="flex-1 overflow-hidden group-hover:pl-1 transition-all">
                <div class="text-sm font-bold text-white truncate group-hover:text-waveLight">{user.username}</div>
                <div class="text-[10px] text-white/40 truncate font-semibold uppercase tracking-wider">{user.skill_level || 'Surfer'}</div>
              </div>
              <svg class="w-4 h-4 text-white/30 group-hover:text-waveLight transition-colors flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
            </button>

            <!-- Logout Button -->
            <button class="flex items-center gap-2 w-full px-3 py-2 rounded-xl text-white/40 hover:text-red-400 hover:bg-white/5 transition-colors text-xs font-bold uppercase tracking-wider" on:click={handleLogout}>
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
              Log Out
            </button>
          </div>
        {:else}
          <button class="text-sm font-bold w-full p-3 bg-white/10 hover:bg-white/20 rounded-xl transition-colors text-white" on:click={handleLogout}>
            Back to Login
          </button>
        {/if}
      </aside>

      <!-- Main Content Area -->
      <main class="flex-1 overflow-y-auto bg-ocean-depth relative custom-scrollbar">
        {#if !isGuest}
          <!-- Notifications Bell (Top Right) -->
          <div class="absolute top-[48px] right-8 md:top-[60px] md:right-10 z-50">
            <button class="relative w-10 h-10 flex items-center justify-center rounded-xl bg-white/70 backdrop-blur border border-white shadow-sm hover:bg-white transition-all group" on:click={() => showNotifications = !showNotifications}>
              <svg class="w-5 h-5 text-[#112D26]/70 group-hover:text-[#112D26] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path></svg>
              {#if unreadCount > 0}
                <span class="absolute -top-1.5 -right-1.5 bg-coral text-white text-[10px] font-bold px-1.5 py-0.5 rounded-md shadow-sm min-w-[20px] text-center border border-white/50">{unreadCount}</span>
              {/if}
            </button>
            
            {#if showNotifications}
              <div transition:fly={{y: -10, duration: 200}} class="absolute top-full right-0 mt-3 w-[380px] bg-white/90 backdrop-blur-xl rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] overflow-hidden z-50 border border-white/40">
                <div class="p-4 flex justify-between items-center border-b border-black/5 bg-white/50">
                  <h3 class="font-bold text-[#112D26] text-sm uppercase tracking-wider">Notifications</h3>
                  {#if unreadCount > 0}
                    <button class="text-xs text-wave font-bold hover:underline" on:click={markAllAsRead}>Mark all as read</button>
                  {/if}
                </div>
                <div class="max-h-[400px] overflow-y-auto custom-scrollbar bg-white/30">
                  {#if notifications.length === 0}
                    <div class="p-6 text-center text-[#112D26]/50 text-sm font-medium">No notifications yet</div>
                  {:else}
                    {#each notifications as notif}
                      <button class="w-full text-left p-4 hover:bg-white/60 border-b border-black/5 transition-colors flex gap-3 {notif.is_read ? 'opacity-60' : 'bg-white/40'}" on:click={() => markAsRead(notif)}>
                        <div class="w-10 h-10 rounded-xl bg-wave flex-shrink-0 flex items-center justify-center text-white font-bold text-sm shadow-inner">
                          {notif.sender_name.charAt(0).toUpperCase()}
                        </div>
                        <div class="flex-1">
                          <p class="text-sm text-[#112D26] {notif.is_read ? '' : 'font-bold'} leading-tight">{notif.message}</p>
                          <span class="text-[10px] text-[#112D26]/50 font-bold mt-1 block uppercase tracking-wider">{new Date(notif.created_at).toLocaleDateString()}</span>
                        </div>
                        {#if !notif.is_read}
                          <div class="w-2 h-2 rounded-full bg-coral mt-1.5 flex-shrink-0 shadow-sm"></div>
                        {/if}
                      </button>
                    {/each}
                  {/if}
                </div>
              </div>
            {/if}
          </div>
        {/if}

        {#key activeTab}
          <div in:fly={{ y: 20, duration: 400, delay: 100 }} out:fade={{ duration: 150 }} class="p-8 md:p-10 h-full">
            {#if activeTab === 'dashboard' && !isGuest}
              <Dashboard {user} onNavigate={(tab) => activeTab = tab} />
            {:else if activeTab === 'feed' && !isGuest}
              <h2 class="text-4xl font-display font-bold mb-8 text-[#0F2922] max-w-2xl mx-auto w-full">Session</h2>
              <SocialFeed {user} bind:focusPostId />
            {:else if activeTab === 'community' && !isGuest}
              <h2 class="text-4xl font-display font-bold mb-8 text-[#0F2922]">Community</h2>
              <Community {user} />
            {:else if activeTab === 'hazard' && !isGuest}
              <h2 class="text-4xl font-display font-bold mb-8 text-coral">Hazard Alert</h2>
              <Hazard {user} />
            {:else if activeTab === 'surfing'}
              <h2 class="text-4xl font-display font-bold mb-8 text-[#0F2922]">Surf Spots</h2>
              <Surfing {user} {isGuest} />
            {:else if activeTab === 'profile' && !isGuest}
              <h2 class="text-4xl font-display font-bold mb-8 text-[#0F2922]">My Profile</h2>
              <MyProfile {user} on:userUpdated={(e) => user = e.detail} />
            {/if}
          </div>
        {/key}
      </main>
      
    </div>
  </div>
{/if}

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 8px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: rgba(17, 45, 38, 0.2);
    border-radius: 20px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background-color: rgba(17, 45, 38, 0.4);
  }
</style>
