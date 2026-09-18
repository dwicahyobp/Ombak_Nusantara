<script>
  import { onMount } from 'svelte';
  import { slide, fade } from 'svelte/transition';
  import { addToast } from './stores/toast.js';
  import { INDO_SURF_SPOTS } from './surfSpots.js';
  
  export let user;
  export let focusPostId = null;
  
  let posts = [];
  let location = '';
  let caption = '';
  let activeFilter = 'Session';
  let mediaFiles = [];
  let posting = false;
  let loadingPosts = true;
  let commentInputs = {};
  let translatedTexts = {};
  let translatingIds = {};
  let searchQuery = '';
  let commentsExpanded = {};
  
  let lightboxMedia = null;
  let animatingLikes = {};
  
  function openLightbox(url) {
    lightboxMedia = url;
  }
  function closeLightbox() {
    lightboxMedia = null;
  }
  
  function toggleComments(postId) {
    commentsExpanded[postId] = !commentsExpanded[postId];
  }
  
  let spotSuggestions = [];
  let showSuggestions = false;
  let searchTimeout = null;
  
  function handleLocationInput(e) {
    location = e.target.value;
    if (searchTimeout) clearTimeout(searchTimeout);
    
    if (location.trim().length < 2) {
      spotSuggestions = [];
      showSuggestions = false;
      return;
    }
    
    searchTimeout = setTimeout(async () => {
      // 1. Search locally
      const queryLower = location.toLowerCase();
      let localMatches = INDO_SURF_SPOTS.filter(s => 
        s.name.toLowerCase().includes(queryLower) || s.region.toLowerCase().includes(queryLower)
      ).slice(0, 5);
      
      let spots = localMatches.map(s => ({
        name: s.name,
        region: s.region
      }));
      
      // 2. Search API to fill the rest up to 5
      if (spots.length < 5) {
        try {
          const res = await fetch(`https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?f=json&singleLine=${encodeURIComponent(location)}&sourceCountry=ID&maxLocations=${5 - spots.length}`);
          if (res.ok) {
            const data = await res.json();
            if (data && data.candidates) {
              data.candidates.forEach(r => {
                const parts = r.address.split(',');
                const apiName = parts[0].trim();
                if (!spots.find(s => s.name === apiName)) {
                  spots.push({
                    name: apiName,
                    region: parts.slice(1).join(', ').trim() || 'Indonesia'
                  });
                }
              });
            }
          }
        } catch (e) {
          console.error("Geocoding error:", e);
        }
      }
      
      spotSuggestions = spots;
      showSuggestions = spotSuggestions.length > 0;
    }, 400);
  }
  
  function selectSpot(spot) {
    location = `${spot.name}, ${spot.region}`;
    spotSuggestions = [];
    showSuggestions = false;
  }
  
  let mentionSuggestions = [];
  let showMentionSuggestions = false;
  let mentionSearchTimeout = null;
  let activeMentionType = null;
  let activeMentionPostId = null;

  async function handleTextInput(e, type, postId = null) {
    const val = e.target.value;
    const cursorPosition = e.target.selectionStart;
    
    // update bind values manually since on:input runs after bind
    if (type === 'caption') caption = val;
    else if (type === 'comment') commentInputs[postId] = val;

    const textBeforeCursor = val.substring(0, cursorPosition);
    const words = textBeforeCursor.split(/[\s\n]+/);
    const currentWord = words[words.length - 1];
    
    if (currentWord.startsWith('@') && currentWord.length > 1) {
      const query = currentWord.substring(1);
      if (mentionSearchTimeout) clearTimeout(mentionSearchTimeout);
      mentionSearchTimeout = setTimeout(async () => {
        try {
          const res = await fetch(`/api/social/users/search?q=${encodeURIComponent(query)}`);
          if (res.ok) {
            const users = await res.json();
            if (users.length > 0) {
              mentionSuggestions = users;
              showMentionSuggestions = true;
              activeMentionType = type;
              activeMentionPostId = postId;
            } else {
              showMentionSuggestions = false;
            }
          }
        } catch (err) {}
      }, 300);
    } else {
      showMentionSuggestions = false;
    }
  }

  function selectMention(userObj) {
    let text = activeMentionType === 'caption' ? caption : commentInputs[activeMentionPostId];
    
    // Find the last word starting with @ and replace it
    const parts = text.split(/([\s\n]+)/); // Split keeping delimiters
    for (let i = parts.length - 1; i >= 0; i--) {
      if (parts[i].trim().startsWith('@')) {
        parts[i] = `@${userObj.username}`;
        break;
      }
    }
    
    if (activeMentionType === 'caption') caption = parts.join('') + ' ';
    else commentInputs[activeMentionPostId] = parts.join('') + ' ';
    
    showMentionSuggestions = false;
  }
  
  $: filteredPosts = posts.filter(p => {
    const matchesCategory = p.category === activeFilter;
    if (!searchQuery.trim()) return matchesCategory;
    const query = searchQuery.toLowerCase();
    const matchesSearch = 
      p.location.toLowerCase().includes(query) || 
      p.caption.toLowerCase().includes(query) || 
      p.username.toLowerCase().includes(query);
    return matchesCategory && matchesSearch;
  });
  
  // Dynamic UI Text based on Category
  $: uiConfig = {
    'Session': {
      title: 'Share Your Session',
      spotPlaceholder: 'Surf Spot (e.g., Uluwatu)',
      captionPlaceholder: 'How were the waves? Any epic moments?',
      btnText: 'Post Session'
    }
  }[activeFilter];
  
  let pollInterval;
  
  async function loadFeed() {
    try {
      const res = await fetch('/api/social/posts');
      if (res.ok) {
        posts = await res.json();
        loadingPosts = false;
        
        // Auto-poll if any post is still syncing
        const needsPolling = posts.some(p => (p.category === 'Session' || p.category === 'Alert') && !p.ai_weather_synced);
        if (needsPolling && !pollInterval) {
          pollInterval = setInterval(loadFeed, 3000);
        } else if (!needsPolling && pollInterval) {
          clearInterval(pollInterval);
          pollInterval = null;
        }
      }
    } catch (err) {
      console.error(err);
      loadingPosts = false;
    }
  }
  
  onMount(() => {
    loadFeed();
    return () => { if (pollInterval) clearInterval(pollInterval); }
  });
  
  $: if (focusPostId && posts.length > 0) {
    const targetPost = posts.find(p => p.id === focusPostId);
    if (targetPost && targetPost.category !== activeFilter) {
      activeFilter = targetPost.category;
    }
    
    setTimeout(() => {
      const el = document.getElementById(`post-${focusPostId}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        let bgColor = targetPost?.category === 'Alert' ? 'rgba(244, 63, 94, 0.4)' : targetPost?.category === 'Community' ? 'rgba(34, 197, 94, 0.4)' : 'rgba(0, 180, 216, 0.4)';
        
        el.style.transition = 'background-color 0.5s ease-out';
        el.style.backgroundColor = bgColor;
        
        setTimeout(() => {
          el.style.backgroundColor = '';
        }, 2000);
      }
      focusPostId = null;
    }, 300);
  }
  
  async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error('Upload failed');
    const data = await res.json();
    return data.url;
  }
  
  async function handlePost() {
    if (!caption.trim()) {
      return addToast('Caption is required', 'warning');
    }
    if (activeFilter === 'Session' && mediaFiles.length === 0) {
      return addToast('A photo or video is required to share a Session!', 'warning');
    }
    if (activeFilter !== 'Community' && !location.trim()) {
      return addToast('Location is required for this category', 'warning');
    }
    
    let finalLocation = location.trim();
    if (activeFilter === 'Community' && !finalLocation) {
      finalLocation = 'No Location';
    }
    
    posting = true;
    
    let media_urls_str = null;
    let media_url = null;
    
    if (mediaFiles.length > 0) {
      let uploaded_urls = [];
      for (const file of mediaFiles) {
        uploaded_urls.push(await uploadFile(file));
      }
      media_urls_str = JSON.stringify(uploaded_urls);
      media_url = uploaded_urls[0]; // fallback
    }
    
    try {
      const res = await fetch('/api/social/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, location: finalLocation, caption, category: activeFilter, media_url, media_urls: media_urls_str })
      });
      
      if (!res.ok) throw new Error('Failed to create post');
      
      location = '';
      caption = '';
      mediaFiles = [];
      document.getElementById('fileInput').value = '';
      
      addToast('Posted! Fetching live marine conditions in background.', 'success');
      await loadFeed();
    } catch (e) {
      addToast(e.message, 'error');
    } finally {
      posting = false;
    }
  }
  
  async function handleComment(postId) {
    const content = commentInputs[postId]?.trim();
    if (!content) return;
    
    try {
      const res = await fetch(`/api/social/posts/${postId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, content })
      });
      
      if (!res.ok) throw new Error('Failed to comment');
      
      commentInputs[postId] = '';
      await loadFeed();
    } catch (e) {
      addToast(e.message, 'error');
    }
  }

  async function translatePost(postId, text) {
    if (!text) return;
    translatingIds[postId] = true;
    try {
      const res = await fetch('/api/social/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      if (!res.ok) throw new Error('Translation failed');
      const data = await res.json();
      translatedTexts[postId] = data.translated_text;
    } catch (e) {
      addToast(e.message, 'error');
    } finally {
      translatingIds[postId] = false;
    }
  }
  
  function hideTranslation(postId) {
    delete translatedTexts[postId];
    translatedTexts = { ...translatedTexts };
  }
  
  async function handleDeletePost(postId) {
    if (!confirm('Are you sure you want to delete this post?')) return;
    
    try {
      const res = await fetch(`/api/social/posts/${postId}?user_id=${user.id}`, {
        method: 'DELETE'
      });
      
      if (!res.ok) throw new Error('Failed to delete post');
      
      addToast('Post deleted successfully', 'success');
      await loadFeed();
    } catch (e) {
      addToast(e.message, 'error');
    }
  }

  async function handleDeleteComment(commentId) {
    if (!confirm('Are you sure you want to delete this comment?')) return;
    
    try {
      const res = await fetch(`/api/social/posts/comments/${commentId}?user_id=${user.id}`, {
        method: 'DELETE'
      });
      
      if (!res.ok) throw new Error('Failed to delete comment');
      
      addToast('Comment deleted successfully', 'success');
      await loadFeed();
    } catch (e) {
      addToast(e.message, 'error');
    }
  }

  async function toggleLike(postId) {
    try {
      // Optimistic UI Animation
      const isLiking = !posts.find(p => p.id === postId)?.liked_by_users?.includes(user.id);
      if (isLiking) {
        animatingLikes[postId] = true;
        setTimeout(() => animatingLikes[postId] = false, 500);
      }
      
      const res = await fetch(`/api/social/posts/${postId}/like?user_id=${user.id}`, { method: 'POST' });
      if (res.ok) await loadFeed();
    } catch (e) {}
  }
  
  function parseUrls(str) {
    if (!str) return [];
    try { return JSON.parse(str); } catch (e) { return [str]; }
  }
  
  function formatMentions(text) {
    if (!text) return '';
    let escaped = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return escaped.replace(/@(\w+)/g, '<span class="text-wave font-bold cursor-pointer hover:underline">@$1</span>');
  }
</script>

<div class="space-y-6 max-w-2xl mx-auto w-full">
  <!-- Top Navigation & Search -->
  <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-black/5">
    <div class="flex items-center gap-2 text-wave font-black">
      <span class="text-xl">🏄‍♂️ Session Feed</span>
    </div>
    
    <!-- Search Bar -->
    <div class="relative w-full md:w-64 flex-shrink-0">
      <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg class="w-4 h-4 text-inkSoft" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
      </div>
      <input 
        type="text" 
        bind:value={searchQuery} 
        placeholder="Search spot, user, or caption..." 
        class="input-field !pl-10 !py-2 !text-sm w-full"
      >
    </div>
  </div>

  <!-- Create Post (Contextual to activeFilter) -->
  {#key activeFilter}
    <div transition:fade={{duration: 200}} class="glass-card-3d p-6 space-y-6">
      
      {#if activeFilter === 'Session'}
        <!-- ================= SESSION: VISUAL FIRST ================= -->
        <label class="flex flex-col items-center justify-center w-full min-h-[140px] bg-white/50 hover:bg-white/80 border-2 border-wave/20 border-dashed rounded-2xl cursor-pointer transition-all group relative overflow-hidden">
          {#if mediaFiles.length > 0}
            <div class="absolute inset-0 bg-wave/10 backdrop-blur-sm flex flex-col items-center justify-center transition-all">
              <span class="text-4xl drop-shadow-sm">📸</span>
              <span class="text-sm font-bold text-ink mt-2">{mediaFiles.length} File(s) Ready to Upload</span>
              <span class="text-[10px] text-inkSoft mt-1">(Click to change files)</span>
            </div>
          {:else}
            <div class="flex flex-col items-center text-wave group-hover:scale-110 transition-transform">
              <svg class="w-14 h-14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
              <span class="text-xs text-inkSoft mt-2 font-medium tracking-wide uppercase">Upload Photo / Video</span>
            </div>
          {/if}
          <input type="file" id="fileInput" multiple accept="image/*,video/*" class="hidden" on:change={(e) => mediaFiles = Array.from(e.target.files)}>
        </label>

        <div class="space-y-4 relative mt-6">
          <textarea value={caption} on:input={(e) => handleTextInput(e, 'caption')} rows="2" class="input-field py-4 resize-y text-2xl font-script bg-white/60 focus:bg-white" placeholder={uiConfig.captionPlaceholder}></textarea>
          
          {#if showMentionSuggestions && activeMentionType === 'caption'}
            <ul class="absolute top-12 z-50 w-full md:w-1/2 bg-surface border border-black/10 rounded-xl max-h-48 overflow-y-auto shadow-glass">
              {#each mentionSuggestions as mu}
                <li>
                  <button class="w-full flex items-center gap-3 px-4 py-3 text-sm text-ink hover:bg-surfaceDeep transition-colors border-b border-black/5" on:click={() => selectMention(mu)}>
                    {#if mu.profile_pic_url}
                      <img src={mu.profile_pic_url} alt="Profile" class="w-8 h-8 rounded-full object-cover">
                    {:else}
                      <div class="w-8 h-8 rounded-full bg-wave text-white flex items-center justify-center font-bold">{mu.username.charAt(0).toUpperCase()}</div>
                    {/if}
                    {mu.username}
                  </button>
                </li>
              {/each}
            </ul>
          {/if}
          
          <div class="flex flex-col md:flex-row gap-4 items-center">
            <div class="relative flex-1 w-full">
              <input type="text" value={location} on:input={handleLocationInput} class="input-field py-3 text-sm w-full" placeholder={uiConfig.spotPlaceholder} on:focus={() => {if(spotSuggestions.length) showSuggestions = true;}}>
              {#if showSuggestions}
                <ul class="absolute bottom-full mb-2 z-50 w-full bg-surface border border-black/10 rounded-xl max-h-48 overflow-y-auto shadow-glass">
                  {#each spotSuggestions as spot}
                    <li>
                      <button class="w-full text-left px-4 py-3 text-sm text-ink hover:bg-surfaceDeep transition-colors border-b border-black/5" on:click={() => selectSpot(spot)}>
                        <span class="block font-semibold">📍 {spot.name}</span>
                        <span class="block text-xs text-inkSoft pl-5">{spot.region}</span>
                      </button>
                    </li>
                  {/each}
                </ul>
              {/if}
            </div>
            
            <button class="btn-primary py-3 px-8 whitespace-nowrap text-sm font-bold tracking-wide shadow-lg" on:click={handlePost} disabled={posting}>
              {posting ? 'Posting...' : uiConfig.btnText}
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/key}

  <!-- Feed -->
  <div class="space-y-8 mt-8">
    {#if loadingPosts}
      <!-- Skeleton Shimmer Cards -->
      {#each Array(3) as _}
        <div class="glass-card flex flex-col space-y-4 animate-pulse border border-black/5 rounded-2xl p-6">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-black/10"></div>
            <div class="space-y-2">
              <div class="h-4 w-32 bg-black/10 rounded"></div>
              <div class="h-3 w-20 bg-black/10 rounded"></div>
            </div>
          </div>
          <div class="space-y-2 pt-2">
            <div class="h-4 w-full bg-black/10 rounded"></div>
            <div class="h-4 w-5/6 bg-black/10 rounded"></div>
          </div>
          <div class="w-full h-64 bg-black/10 rounded-xl mt-4"></div>
          <div class="flex gap-4 pt-4 border-t border-black/5">
            <div class="h-6 w-20 bg-black/10 rounded"></div>
            <div class="h-6 w-24 bg-black/10 rounded"></div>
          </div>
        </div>
      {/each}
    {:else if filteredPosts.length === 0}
      <div class="glass-card-3d text-center py-20 flex flex-col items-center justify-center gap-4 bg-white/40">
        <div class="text-6xl opacity-50 hover-float animate-bounce">🌊</div>
        <h3 class="text-3xl font-display font-bold text-ink">No posts yet</h3>
        <p class="text-lg font-medium text-inkSoft max-w-sm mx-auto">Be the first to share your surfing session with the community!</p>
      </div>
    {:else}
      {#each filteredPosts as post (post.id)}
        <div id="post-{post.id}" transition:slide={{ duration: 400 }} class="p-5 md:p-7 rounded-3xl bg-white/70 backdrop-blur-2xl border border-white/60 shadow-xl shadow-wave/5 space-y-4 relative transition-all duration-300">
          {#if post.user_id === user.id}
            <button 
              class="absolute top-5 right-5 text-inkSoft hover:text-warning transition-colors"
              on:click={() => handleDeletePost(post.id)}
              title="Delete Post"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
            </button>
          {/if}
          <div>
            <div class="flex items-center gap-3.5 mb-4">
              {#if post.profile_pic_url}
                <img src={post.profile_pic_url} alt="Profile" class="w-12 h-12 rounded-full object-cover ring-2 ring-wave/20 shadow-sm">
              {:else}
                <div class="w-12 h-12 rounded-full bg-gradient-to-br from-wave to-deep flex items-center justify-center text-white font-bold text-lg shadow-sm ring-2 ring-wave/20">
                  {post.username.charAt(0).toUpperCase()}
                </div>
              {/if}
              <div class="flex flex-col justify-center">
                <div class="flex items-center gap-2">
                  <span class="font-bold text-ink text-base tracking-tight">{post.username}</span>
                  <span class="text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider {post.category === 'Alert' ? 'bg-warning/10 text-warning border border-warning/30 animate-pulse' : post.category === 'Community' ? 'bg-safe/10 text-safe border border-safe/30' : 'bg-wave/10 text-wave border border-wave/30'}">
                    {post.category === 'Alert' ? '⚠️ Alert' : post.category === 'Community' ? '🏕️ Community' : '🏄‍♂️ Session'}
                  </span>
                </div>
                <p class="text-[11px] text-inkSoft uppercase font-semibold tracking-wider mt-0.5 flex items-center gap-1">
                  <svg class="w-3 h-3 text-wave" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                  <span class={post.location === 'No Location' ? 'opacity-70' : 'text-deep font-bold'}>{post.location}</span>
                </p>
              </div>
            </div>
            <p class="mt-3 text-base md:text-[17px] leading-relaxed font-sans pr-4 whitespace-pre-wrap text-ink/90">{@html formatMentions(post.caption)}</p>
          </div>
          
          <!-- Media Gallery (Pinterest Style Slide) -->
          {#if post.media_urls || post.media_url}
            {@const mediaList = parseUrls(post.media_urls || `["${post.media_url}"]`)}
            
            {#if mediaList.length === 1}
              <!-- Single Media: Premium 4/3 Aspect Ratio -->
              <div class="py-2 w-full">
                {#if mediaList[0].match(/\.(mp4|webm|ogg)$/i)}
                  <!-- svelte-ignore a11y-media-has-caption -->
                  <video src={mediaList[0]} controls class="w-full max-h-[600px] object-cover aspect-[4/3] md:aspect-auto md:max-h-[700px] rounded-2xl bg-black/5 shadow-md border border-white/40"></video>
                {:else}
                  <!-- svelte-ignore a11y-click-events-have-key-events -->
                  <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
                  <img src={mediaList[0]} alt="Post media" class="w-full object-cover aspect-[4/3] rounded-2xl bg-black/5 shadow-md hover:shadow-lg border border-white/40 transition-all duration-300 cursor-zoom-in" on:click={() => openLightbox(mediaList[0])} />
                {/if}
              </div>
            {:else}
              <!-- Multiple Media: Snap Carousel -->
              <div class="flex overflow-x-auto gap-3 snap-x snap-mandatory scrollbar-hide py-2 px-1">
                {#each mediaList as url}
                  <div class="snap-center flex-shrink-0 w-[90%] md:w-[75%]">
                    {#if url.match(/\.(mp4|webm|ogg)$/i)}
                      <!-- svelte-ignore a11y-media-has-caption -->
                      <video src={url} controls class="w-full object-cover aspect-[4/3] rounded-2xl bg-black/5 shadow-md border border-white/40"></video>
                    {:else}
                      <!-- svelte-ignore a11y-click-events-have-key-events -->
                      <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
                      <div class="relative group cursor-zoom-in overflow-hidden rounded-2xl border border-white/40 shadow-md" on:click={() => openLightbox(url)}>
                        <img src={url} alt="Post media" class="w-full object-cover aspect-[4/3] bg-black/5 group-hover:scale-105 transition-transform duration-700" />
                        <div class="absolute inset-0 bg-black/0 group-hover:bg-white/10 transition-colors duration-300"></div>
                      </div>
                    {/if}
                  </div>
                {/each}
              </div>
            {/if}
          {/if}
          
          {#if translatedTexts[post.id]}
            <div class="p-3 bg-wave/5 border border-wave/20 rounded-lg text-sm text-ink italic relative mt-2">
              <span class="absolute top-2 right-8 text-xs text-wave">Indonesian</span>
              <button class="absolute top-1.5 right-2 text-inkSoft hover:text-ink transition-colors" on:click={() => hideTranslation(post.id)}>
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
              </button>
              {translatedTexts[post.id]}
            </div>
          {:else if post.caption}
            <button 
              class="text-xs font-bold text-wave hover:text-deep transition-colors flex items-center gap-1"
              on:click={() => translatePost(post.id, post.caption)}
              disabled={translatingIds[post.id]}
            >
              {translatingIds[post.id] ? '⏳ Translating...' : '🌐 Translate to Indonesian'}
            </button>
          {/if}
          
          {#if post.category === 'Session' || post.category === 'Alert'}
            {#if post.ai_weather_synced}
              <div class="bg-gradient-to-r from-wave/10 to-deep/5 py-2.5 px-4 rounded-xl text-sm border border-wave/20 flex flex-wrap md:flex-nowrap items-center justify-between gap-3 shadow-inner">
                <div class="flex items-center gap-2 flex-shrink-0">
                  <span class="relative flex h-2.5 w-2.5">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-wave opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-wave"></span>
                  </span>
                  <strong class="text-deep font-display text-sm tracking-wide">Live Spot Info</strong>
                </div>
                <div class="flex items-center gap-3 md:gap-5 flex-1 justify-end md:justify-center flex-wrap">
                  <div class="flex items-center gap-1.5"><span class="text-[10px] text-inkSoft uppercase font-bold bg-white/60 px-1.5 py-0.5 rounded">Wind</span> <span class="font-bold text-deep text-xs truncate max-w-[120px] md:max-w-[200px]" title={post.wind_conditions}>{post.wind_conditions}</span></div>
                  <div class="flex items-center gap-1.5"><span class="text-[10px] text-inkSoft uppercase font-bold bg-white/60 px-1.5 py-0.5 rounded">Swell</span> <span class="font-bold text-deep text-xs truncate max-w-[120px] md:max-w-[200px]" title={post.swell_info}>{post.swell_info}</span></div>
                  <div class="flex items-center gap-1.5"><span class="text-[10px] text-inkSoft uppercase font-bold bg-white/60 px-1.5 py-0.5 rounded">Waves</span> <span class="font-bold text-deep text-xs truncate max-w-[120px] md:max-w-[200px]" title={post.tide_info}>{post.tide_info}</span></div>
                </div>
              </div>
            {:else}
              <div class="flex items-center gap-4 bg-surfaceDeep p-3 rounded-lg border border-black/5">
                <div class="wave-loader">
                  <div class="bg-wave"></div>
                  <div class="bg-wave"></div>
                  <div class="bg-wave"></div>
                  <div class="bg-wave"></div>
                  <div class="bg-wave"></div>
                </div>
                <span class="text-xs text-wave font-medium tracking-wide">Syncing satellite data...</span>
              </div>
            {/if}
          {/if}
          
          <!-- Comments & Likes Section -->
          <div class="pt-4 border-t border-black/5 space-y-3">
            <div class="flex items-center gap-4 mb-2">
              <button class="flex items-center gap-1 text-sm font-bold {post.liked_by_users?.includes(user.id) ? 'text-coral' : 'text-inkSoft hover:text-ink'} transition-colors group" on:click={() => toggleLike(post.id)}>
                <span class="{animatingLikes[post.id] ? 'animate-like-pop' : 'group-hover:scale-110'} inline-block transition-transform duration-300">
                  {post.liked_by_users?.includes(user.id) ? '❤️' : '🤍'}
                </span>
                {post.likes_count || 0} Likes
              </button>
              <div class="text-sm text-inkSoft font-bold">💬 {post.comments?.length || 0} Comments</div>
            </div>
            
            {#if post.comments && post.comments.length > 0}
              <div class="space-y-3 mt-4">
                {#each (commentsExpanded[post.id] ? post.comments : post.comments.slice(-2)) as comment}
                  <div class="flex items-start gap-3 bg-surface p-3 rounded-xl transition-all border border-black/5 shadow-sm relative group/comment">
                    {#if comment.user_id === user.id}
                      <button class="absolute top-2 right-2 p-1 text-inkSoft hover:text-coral opacity-0 group-hover/comment:opacity-100 transition-all" on:click|stopPropagation={() => handleDeleteComment(comment.id)} title="Delete Comment">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                      </button>
                    {/if}
                    {#if comment.profile_pic_url}
                      <img src={comment.profile_pic_url} alt="Profile" class="w-8 h-8 rounded-full object-cover mt-0.5">
                    {:else}
                      <div class="w-8 h-8 rounded-full bg-wave flex items-center justify-center text-white text-xs font-bold mt-0.5">
                        {comment.username.charAt(0).toUpperCase()}
                      </div>
                    {/if}
                    <div class="flex-1 text-sm pt-1 pr-6">
                      <strong class="text-deep mr-1">{comment.username}</strong> 
                      <span class="text-ink whitespace-pre-wrap leading-relaxed">{@html formatMentions(comment.content)}</span>
                    </div>
                  </div>
                {/each}
              </div>
              
              {#if post.comments.length > 2}
                <button class="text-xs text-inkSoft hover:text-ink font-semibold transition-colors mt-2" on:click={() => toggleComments(post.id)}>
                  {commentsExpanded[post.id] ? 'Hide comments' : `View all ${post.comments.length} comments`}
                </button>
              {/if}
            {/if}
            
            <div class="flex gap-2 relative">
              <input 
                type="text" 
                value={commentInputs[post.id] || ''} 
                class="input-field py-2 text-sm bg-white border border-black/10 focus:border-wave" 
                placeholder="Write a comment..."
                on:input={(e) => handleTextInput(e, 'comment', post.id)}
                on:keydown={(e) => e.key === 'Enter' && handleComment(post.id)}
              >
              <button class="btn-primary py-2 px-4 shadow-sm" on:click={() => handleComment(post.id)}>Send</button>
              
              {#if showMentionSuggestions && activeMentionType === 'comment' && activeMentionPostId === post.id}
                <ul class="absolute bottom-full mb-2 z-50 w-[80%] bg-surface border border-black/10 rounded-xl max-h-48 overflow-y-auto shadow-glass">
                  {#each mentionSuggestions as mu}
                    <li>
                      <button class="w-full flex items-center gap-3 px-4 py-3 text-sm text-ink hover:bg-surfaceDeep transition-colors border-b border-black/5" on:click={() => selectMention(mu)}>
                        {#if mu.profile_pic_url}
                          <img src={mu.profile_pic_url} alt="Profile" class="w-8 h-8 rounded-full object-cover">
                        {:else}
                          <div class="w-8 h-8 rounded-full bg-wave text-white flex items-center justify-center font-bold">{mu.username.charAt(0).toUpperCase()}</div>
                        {/if}
                        {mu.username}
                      </button>
                    </li>
                  {/each}
                </ul>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    {/if}
  </div>
</div>

{#if lightboxMedia}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div transition:fade={{duration: 200}} class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-md" on:click={closeLightbox}>
    <button class="absolute top-6 right-6 text-white hover:text-white bg-black/40 hover:bg-black/60 p-3 rounded-full backdrop-blur-md transition-all duration-300" on:click={closeLightbox}>
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
    </button>
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
    <img transition:slide src={lightboxMedia} alt="Fullscreen Media" class="max-w-[95vw] max-h-[90vh] object-contain rounded-lg shadow-2xl cursor-default" on:click|stopPropagation />
  </div>
{/if}
