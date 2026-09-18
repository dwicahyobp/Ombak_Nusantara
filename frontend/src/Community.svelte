<script>
  import { onMount } from 'svelte';
  import { fade, slide } from 'svelte/transition';
  import { addToast } from './stores/toast.js';
  import { INDO_SURF_SPOTS } from './surfSpots.js';

  export let user;
  
  let activeTab = 'market'; // 'market', 'meetups', 'threads'
  let items = [];
  let filteredItems = [];
  let loading = false;
  let searchQuery = '';
  
  // Modal State
  let showModal = false;
  
  // Form fields
  let title = '';
  let content = '';
  
  // Market specific
  let price = '';
  let condition = 'Used - Good';
  let marketLocation = 'Canggu';
  let fileInput;
  let selectedFile = null;
  let imagePreviewUrl = null;
  
  // Meetup specific
  let meetupLocation = '';
  let meetupDate = '';
  let meetupTime = '';
  let meetupSkill = 'All Levels';

  // Universal expanded state for comments
  let expandedItem = null; // item ID
  let replyContent = '';
  let postingReply = false;
  
  // Predictive Location Search
  let spotSuggestions = [];
  let showSuggestions = false;
  let searchTimeout = null;
  let activeLocationField = '';
  
  // Mention System
  let mentionSuggestions = [];
  let showMentionSuggestions = false;
  let mentionSearchTimeout = null;
  let activeMentionPostId = null;
  
  async function loadData() {
    loading = true;
    try {
      let endpoint = '';
      if (activeTab === 'threads') endpoint = '/api/social/threads';
      else if (activeTab === 'market') endpoint = '/api/social/market';
      else if (activeTab === 'meetups') endpoint = '/api/social/meetups';
      
      const res = await fetch(endpoint);
      if (res.ok) {
        items = await res.json();
      } else {
        addToast('Failed to load data', 'error');
      }
    } catch (e) {
      addToast(e.message, 'error');
    } finally {
      loading = false;
    }
  }
  
  onMount(loadData);
  
  $: if (activeTab) {
    expandedItem = null; // collapse on tab switch
    searchQuery = ''; // reset search on tab switch
    loadData();
  }
  
  // Predictive Search logic
  $: {
    if (!searchQuery.trim()) {
      filteredItems = items;
    } else {
      const q = searchQuery.toLowerCase();
      filteredItems = items.filter(item => {
        const titleMatch = item.title?.toLowerCase().includes(q);
        const descMatch = (item.content || item.description)?.toLowerCase().includes(q);
        const locMatch = item.location?.toLowerCase().includes(q);
        const userMatch = item.username?.toLowerCase().includes(q);
        return titleMatch || descMatch || locMatch || userMatch;
      });
    }
  }
  
  function resetForm() {
    title = '';
    content = '';
    price = '';
    condition = 'Used - Good';
    marketLocation = 'Canggu';
    meetupLocation = '';
    meetupDate = '';
    meetupTime = '';
    meetupSkill = 'All Levels';
    selectedFile = null;
    imagePreviewUrl = null;
  }

  function openModal() {
    resetForm();
    showModal = true;
  }

  function closeModal() {
    showModal = false;
    spotSuggestions = [];
    showSuggestions = false;
    showMentionSuggestions = false;
  }

  async function handleDeleteItem(itemId) {
    if (!confirm('Are you sure you want to delete this post?')) return;
    
    try {
      let endpoint = '';
      if (activeTab === 'threads') endpoint = `/api/social/threads/${itemId}?user_id=${user.id}`;
      else if (activeTab === 'market') endpoint = `/api/social/market/${itemId}?user_id=${user.id}`;
      else if (activeTab === 'meetups') endpoint = `/api/social/meetups/${itemId}?user_id=${user.id}`;

      const res = await fetch(endpoint, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete item');
      
      addToast('Item deleted successfully', 'success');
      loadData();
    } catch (e) {
      addToast(e.message, 'error');
    }
  }

  async function handleDeleteComment(commentId) {
    if (!confirm('Are you sure you want to delete this comment?')) return;
    
    try {
      let endpoint = '';
      if (activeTab === 'threads') endpoint = `/api/social/threads/comments/${commentId}?user_id=${user.id}`;
      else if (activeTab === 'market') endpoint = `/api/social/market/comments/${commentId}?user_id=${user.id}`;
      else if (activeTab === 'meetups') endpoint = `/api/social/meetups/comments/${commentId}?user_id=${user.id}`;

      const res = await fetch(endpoint, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete comment');
      
      addToast('Comment deleted successfully', 'success');
      loadData();
    } catch (e) {
      addToast(e.message, 'error');
    }
  }

  function handleTextInput(e, postId) {
    const val = e.target.value;
    const cursorPosition = e.target.selectionStart;
    
    replyContent = val;

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
    let text = replyContent;
    const parts = text.split(/([\s\n]+)/);
    for (let i = parts.length - 1; i >= 0; i--) {
      if (parts[i].trim().startsWith('@')) {
        parts[i] = `@${userObj.username}`;
        break;
      }
    }
    replyContent = parts.join('') + ' ';
    showMentionSuggestions = false;
  }
  
  function formatMentions(text) {
    if (!text) return '';
    let escaped = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return escaped.replace(/@(\w+)/g, '<span class="text-wave font-bold cursor-pointer hover:underline">@$1</span>');
  }

  function handleLocationInput(e, field) {
    if (field === 'market') marketLocation = e.target.value;
    else if (field === 'meetups') meetupLocation = e.target.value;
    
    activeLocationField = field;
    
    if (searchTimeout) clearTimeout(searchTimeout);
    
    let query = e.target.value;
    if (query.trim().length < 2) {
      spotSuggestions = [];
      showSuggestions = false;
      return;
    }
    
    searchTimeout = setTimeout(async () => {
      const queryLower = query.toLowerCase();
      let localMatches = INDO_SURF_SPOTS.filter(s => 
        s.name.toLowerCase().includes(queryLower) || s.region.toLowerCase().includes(queryLower)
      ).slice(0, 5);
      
      let spots = localMatches.map(s => ({
        name: s.name,
        region: s.region
      }));
      
      if (spots.length < 5) {
        try {
          const res = await fetch(`https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?f=json&singleLine=${encodeURIComponent(query)}&sourceCountry=ID&maxLocations=${5 - spots.length}`);
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
    let loc = `${spot.name}, ${spot.region}`;
    if (activeLocationField === 'market') marketLocation = loc;
    else if (activeLocationField === 'meetups') meetupLocation = loc;
    spotSuggestions = [];
    showSuggestions = false;
  }

  function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    selectedFile = file;
    imagePreviewUrl = URL.createObjectURL(file);
  }
  
  async function handlePost() {
    if (!title.trim()) return addToast('Title is required', 'warning');
    
    let endpoint = '';
    let payload = { user_id: user.id };
    
    if (activeTab === 'threads') {
      if (!content.trim()) return addToast('Content is required', 'warning');
      endpoint = '/api/social/threads';
      payload.title = title;
      payload.content = content;
      payload.category = 'General';
    } 
    else if (activeTab === 'market') {
      if (!price) return addToast('Price is required', 'warning');
      if (!content.trim()) return addToast('Description is required', 'warning');
      
      loading = true;
      let uploadedUrl = null;
      // Upload image first if selected
      if (selectedFile) {
        const formData = new FormData();
        formData.append('file', selectedFile);
        try {
          const upRes = await fetch('/api/upload', {
            method: 'POST',
            body: formData
          });
          if (!upRes.ok) throw new Error('Upload failed');
          const upData = await upRes.json();
          uploadedUrl = upData.url;
        } catch (e) {
          loading = false;
          return addToast('Failed to upload image', 'error');
        }
      }

      endpoint = '/api/social/market';
      payload.title = title;
      payload.price = parseFloat(price).toString();
      payload.location = marketLocation;
      payload.condition = condition;
      payload.description = content;
      payload.image_url = uploadedUrl;
    }
    else if (activeTab === 'meetups') {
      if (!meetupLocation || !meetupDate || !meetupTime || !content.trim()) return addToast('All fields are required', 'warning');
      endpoint = '/api/social/meetups';
      payload.title = title;
      payload.location = meetupLocation;
      payload.date = meetupDate;
      payload.time = meetupTime;
      payload.description = content;
      payload.skill_level = meetupSkill;
    }
    
    loading = true;
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) throw new Error('Failed to post');
      
      addToast('Posted successfully', 'success');
      closeModal();
      loadData();
    } catch (e) {
      addToast(e.message, 'error');
    } finally {
      loading = false;
    }
  }

  async function handleJoinMeetup(meetupId) {
    try {
      const res = await fetch(`/api/social/meetups/${meetupId}/join?user_id=${user.id}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'success') {
          addToast('Joined meetup!', 'success');
          loadData();
        } else {
          addToast('You already joined this meetup.', 'info');
        }
      }
    } catch (e) {
      addToast('Failed to join', 'error');
    }
  }

  async function handlePostReply(itemId) {
    if (!replyContent.trim()) return;
    postingReply = true;
    try {
      let endpoint = '';
      if (activeTab === 'threads') endpoint = `/api/social/threads/${itemId}/comments`;
      else if (activeTab === 'market') endpoint = `/api/social/market/${itemId}/comments`;
      else if (activeTab === 'meetups') endpoint = `/api/social/meetups/${itemId}/comments`;

      const payload = { user_id: user.id, content: replyContent };
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error();
      addToast('Comment posted', 'success');
      replyContent = '';
      loadData(); // reload thread data
    } catch (e) {
      addToast('Failed to post comment', 'error');
    } finally {
      postingReply = false;
    }
  }

  async function markAsSold(itemId) {
    if (!confirm("Are you sure you want to mark this item as sold?")) return;
    try {
      const res = await fetch(`/api/social/market/${itemId}/sold?user_id=${user.id}`, { method: 'POST' });
      if (res.ok) {
        addToast('Item marked as sold!', 'success');
        loadData();
      } else {
        addToast('Failed to update status', 'error');
      }
    } catch (e) {
      addToast('Failed to update status', 'error');
    }
  }

  function formatRp(value) {
    if (!value) return "Rp 0";
    return "Rp " + parseFloat(value).toLocaleString('id-ID');
  }

  function formatDateDayMonth(dateStr) {
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) throw new Error();
      const day = d.getDate().toString().padStart(2, '0');
      const month = d.toLocaleString('en-US', { month: 'short' }).toUpperCase();
      return { day, month };
    } catch {
      return { day: '??', month: '???' };
    }
  }

  function getInitial(name) {
    return name ? name.charAt(0).toUpperCase() : 'U';
  }
</script>

<div class="space-y-6 relative min-h-screen pb-24">
  <!-- Top Bar: Navigation Pills & Search -->
  <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
    <!-- Navigation Pill -->
    <div class="inline-flex bg-surfaceDeep/60 backdrop-blur-sm p-1.5 rounded-[20px] shadow-sm w-fit">
      <button 
        class="px-5 py-2.5 rounded-2xl text-sm font-bold transition-all {activeTab === 'market' ? 'bg-white text-wave shadow-sm border border-wave' : 'text-inkSoft hover:text-ink'}"
        on:click={() => activeTab = 'market'}
      >
        Marketplace
      </button>
      <button 
        class="px-5 py-2.5 rounded-2xl text-sm font-bold transition-all {activeTab === 'meetups' ? 'bg-white text-wave shadow-sm border border-wave' : 'text-inkSoft hover:text-ink'}"
        on:click={() => activeTab = 'meetups'}
      >
        Meetups
      </button>
      <button 
        class="px-5 py-2.5 rounded-2xl text-sm font-bold transition-all {activeTab === 'threads' ? 'bg-white text-wave shadow-sm border border-wave' : 'text-inkSoft hover:text-ink'}"
        on:click={() => activeTab = 'threads'}
      >
        Discussions
      </button>
    </div>

    <!-- Predictive Search Bar -->
    <div class="relative w-full md:max-w-xs">
      <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg class="w-4 h-4 text-inkSoft" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
      </div>
      <input 
        type="text" 
        bind:value={searchQuery}
        placeholder="Search {activeTab}..." 
        class="input-field py-2.5 pl-9 pr-4 w-full bg-white shadow-sm border-black/5 text-sm transition-all focus:ring-2 focus:ring-wave/20"
      />
    </div>
  </div>

  <!-- Feed List -->
  <div class={activeTab === 'market' ? "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 items-start" : "space-y-4"}>
    {#if loading && (!items || items.length === 0)}
      <div class="col-span-full flex justify-center py-10">
        <div class="w-8 h-8 border-4 border-wave border-t-transparent rounded-full animate-spin"></div>
      </div>
    {:else if !filteredItems || filteredItems.length === 0}
      <div class="col-span-full bg-white/50 rounded-[24px] text-center py-12 border-dashed border-2 border-black/10">
        <div class="text-4xl mb-4 opacity-50">🌊</div>
        {#if searchQuery}
          <p class="text-ink font-bold">No results found for "{searchQuery}"</p>
          <p class="text-inkSoft text-sm">Try adjusting your search terms.</p>
        {:else}
          <p class="text-ink font-bold">No items found.</p>
          <p class="text-inkSoft text-sm">Be the first to post!</p>
        {/if}
      </div>
    {:else}
      {#each filteredItems as item, i}
        {#if activeTab === 'meetups'}
          {@const d = formatDateDayMonth(item.date)}
          {@const isJoined = item.attendees && item.attendees.includes(user.username)}
          <!-- Meetups Layout -->
          <!-- svelte-ignore a11y-click-events-have-key-events -->
          <!-- svelte-ignore a11y-no-static-element-interactions -->
          <div transition:slide class="bg-white rounded-[24px] p-5 shadow-sm border border-black/5 hover:border-black/10 hover:shadow-md transition-all cursor-pointer group" on:click={() => expandedItem = expandedItem === item.id ? null : item.id}>
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div class="flex items-start sm:items-center gap-6">
                <!-- Date Block -->
                <div class="flex flex-col items-center justify-center min-w-[3.5rem] mt-1 sm:mt-0">
                  <span class="text-3xl font-display font-bold text-ink leading-none">{d.day}</span>
                  <span class="text-xs font-medium text-inkSoft tracking-widest mt-1">{d.month}</span>
                </div>
                
                <!-- Content Block -->
                <div class="relative w-full">
                  {#if item.user_id === user.id}
                    <button class="absolute -top-1 -right-4 p-1 text-inkSoft hover:text-coral transition-colors" on:click|stopPropagation={() => handleDeleteItem(item.id)} title="Delete Meetup">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                    </button>
                  {/if}
                  <h3 class="font-bold text-ink text-[17px] mb-1 pr-6">{item.title}</h3>
                  <p class="text-[13px] text-inkSoft font-medium">{item.time} · {item.location}</p>
                  <div class="text-[11px] text-inkSoft mt-1.5 opacity-80 italic line-clamp-2">{item.description}</div>
                  <div class="flex flex-wrap items-center gap-2 mt-3">
                    {#if item.user_id === user.id}
                      <button class="shrink-0 bg-coral/10 text-coral hover:bg-coral hover:text-white px-2 py-0.5 rounded text-[10px] font-bold transition-colors" on:click|stopPropagation={() => handleDeleteItem(item.id)}>
                        Delete
                      </button>
                    {/if}
                    <div class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-surfaceDeep rounded-full text-[10px] font-bold text-inkSoft uppercase tracking-wider">
                      {#if item.profile_pic_url}
                        <img src={item.profile_pic_url} alt="Profile" class="w-4 h-4 rounded-full object-cover">
                      {:else}
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
                      {/if}
                      Organized by: <span class="text-ink">{item.username}</span>
                    </div>
                    <div class="inline-flex items-center gap-1.5 text-[11px] font-bold text-inkSoft group-hover:text-wave transition-colors">
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>
                      {item.comments ? item.comments.length : 0} Comments
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="flex items-center justify-between sm:justify-end gap-6 sm:w-auto w-full pt-4 sm:pt-0 border-t border-black/5 sm:border-0 mt-4 sm:mt-0" on:click|stopPropagation>
                <div class="flex -space-x-2">
                  {#if item.attendees && item.attendees.length > 0}
                    {#each item.attendees.slice(0, 3) as att, idx}
                      <div class="w-8 h-8 rounded-full text-white flex items-center justify-center text-[10px] font-bold border-[2px] border-white z-{(3-idx)*10}" 
                           class:bg-wave={idx%3===0} class:bg-coral={idx%3===1} class:bg-deep={idx%3===2} title={att}>
                        {getInitial(att)}
                      </div>
                    {/each}
                    {#if item.attendees.length > 3}
                      <div class="w-8 h-8 rounded-full bg-inkSoft text-white flex items-center justify-center text-[10px] font-bold border-[2px] border-white z-0">
                        +{item.attendees.length - 3}
                      </div>
                    {/if}
                  {:else}
                    <span class="text-xs text-inkSoft italic px-2">No attendees yet</span>
                  {/if}
                </div>
                <button 
                  class="px-6 py-2.5 text-[13px] font-bold rounded-xl shadow-sm transition-colors shrink-0 {isJoined ? 'bg-inkSoft/20 text-inkSoft cursor-default' : 'bg-wave text-white hover:bg-deep'}" 
                  on:click={() => !isJoined && handleJoinMeetup(item.id)}
                  disabled={isJoined}
                >
                  {isJoined ? 'Joined' : 'Join'}
                </button>
              </div>
            </div>

            {#if expandedItem === item.id}
              <div class="mt-4 pt-4 border-t border-black/5 space-y-4" transition:slide|local>
                {#if item.comments && item.comments.length > 0}
                  <div class="space-y-4 mb-4">
                    {#each item.comments as comment}
                      <div class="bg-surface/50 rounded-2xl p-4 relative group/comment">
                        {#if comment.user_id === user.id}
                          <button class="absolute top-3 right-3 p-1 text-inkSoft hover:text-coral opacity-0 group-hover/comment:opacity-100 transition-all" on:click|stopPropagation={() => handleDeleteComment(comment.id)} title="Delete Comment">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                          </button>
                        {/if}
                        <div class="flex items-center gap-2 mb-2 pr-6">
                          {#if comment.profile_pic_url}
                            <img src={comment.profile_pic_url} alt="Profile" class="w-5 h-5 rounded-full object-cover">
                          {:else}
                            <div class="w-5 h-5 rounded-full overflow-hidden bg-wave/20 flex items-center justify-center text-[9px] font-bold text-wave">
                              {getInitial(comment.username)}
                            </div>
                          {/if}
                          <span class="text-xs font-bold text-ink">{comment.username}</span>
                          <span class="text-[10px] text-inkSoft">{new Date(comment.created_at).toLocaleDateString()}</span>
                        </div>
                        <p class="text-sm text-inkSoft pl-7">{@html formatMentions(comment.content)}</p>
                      </div>
                    {/each}
                  </div>
                {:else}
                  <p class="text-xs text-inkSoft italic mb-4">No comments yet. Start the conversation!</p>
                {/if}
                
                <div class="flex gap-2 relative" on:click|stopPropagation>
                  <input type="text" value={expandedItem === item.id ? replyContent : ''} on:input={(e) => handleTextInput(e, item.id)} class="input-field py-2 text-sm w-full bg-surfaceDeep" placeholder="Ask a question or say hi..." on:keydown={(e) => e.key === 'Enter' && handlePostReply(item.id)}/>
                  <button class="px-4 py-2 bg-wave text-white rounded-xl text-sm font-bold hover:bg-deep transition-colors shrink-0 disabled:opacity-50" on:click={() => handlePostReply(item.id)} disabled={postingReply}>
                    Send
                  </button>
                </div>
              </div>
            {/if}
          </div>

        {:else if activeTab === 'market'}
          {@const isOwner = item.user_id === user.id}
          {@const isSold = item.status === 'Sold'}
          <div transition:slide class="bg-white rounded-[24px] p-3 shadow-sm border border-black/5 hover:border-black/10 transition-colors flex flex-col group cursor-pointer relative {isSold ? 'opacity-80' : ''}" on:click={() => expandedItem = expandedItem === item.id ? null : item.id}>
            
            {#if isSold}
              <div class="absolute inset-0 z-10 flex items-center justify-center pointer-events-none">
                <div class="bg-coral text-white font-display font-black text-4xl tracking-widest px-8 py-3 rounded-2xl shadow-2xl -rotate-12 border-4 border-white/20">
                  SOLD
                </div>
              </div>
            {/if}

            <div class="w-full aspect-[4/3] bg-[#E5D9B6] rounded-[20px] relative overflow-hidden mb-4 flex items-center justify-center {isSold ? 'grayscale' : ''}">
              {#if item.image_url}
                <img src={item.image_url} alt={item.title} class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
              {:else}
                <svg class="absolute bottom-4 left-4 w-7 h-7 text-ink/20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 2C12 2 7 8 7 15C7 18 9.5 21 12 21C14.5 21 17 18 17 15C17 8 12 2 12 2Z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 15L12 21"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 18H15"></path></svg>
                <span class="text-ink/20 font-bold text-sm">No Image</span>
              {/if}
              
              <div class="absolute top-3 left-3 bg-white/90 backdrop-blur-sm px-2.5 py-1.5 rounded-full flex items-center gap-1.5 shadow-sm">
                {#if item.profile_pic_url}
                  <img src={item.profile_pic_url} alt="Profile" class="w-5 h-5 rounded-full object-cover shadow-sm">
                {:else}
                  <div class="w-4 h-4 rounded-full bg-wave text-white flex items-center justify-center text-[8px] font-bold">
                    {getInitial(item.username)}
                  </div>
                {/if}
                <span class="text-[10px] font-bold text-ink pr-1">{item.username}</span>
              </div>
            </div>
            
            <div class="px-1 flex flex-col flex-1">
              <div class="flex items-start justify-between gap-2 mb-1">
                <h3 class="font-bold text-[15px] text-ink line-clamp-1">{item.title}</h3>
                <div class="flex gap-2">
                  {#if isOwner}
                    <button class="text-coral hover:underline text-[10px] font-bold" on:click|stopPropagation={() => handleDeleteItem(item.id)}>Delete</button>
                  {/if}
                  {#if isOwner && !isSold}
                    <button class="shrink-0 bg-coral/10 text-coral hover:bg-coral hover:text-white px-2 py-0.5 rounded text-[10px] font-bold transition-colors" on:click|stopPropagation={() => markAsSold(item.id)}>
                      Mark Sold
                    </button>
                  {/if}
                </div>
              </div>
              <p class="font-bold text-[15px] text-ink mb-3">{formatRp(item.price)}</p>
              
              <div class="text-[11px] text-inkSoft mb-4 truncate mt-auto">
                {item.location} • Posted {new Date(item.created_at || Date.now()).toLocaleDateString()}
              </div>
              
              <div class="flex items-center justify-between">
                <span class="inline-block px-3 py-1.5 rounded-lg text-[10px] font-bold tracking-wide bg-surfaceDeep text-deep">
                  {item.condition}
                </span>
                <span class="text-[11px] font-bold text-inkSoft flex items-center gap-1 group-hover:text-wave transition-colors">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>
                  {item.comments ? item.comments.length : 0}
                </span>
              </div>
            </div>

            <!-- Marketplace Accordion Comments Section -->
            {#if expandedItem === item.id}
              <div class="mt-4 pt-4 border-t border-black/5 space-y-4 px-1" transition:slide|local on:click|stopPropagation>
                <!-- Description Reminder -->
                <div class="bg-surfaceDeep rounded-xl p-3 mb-4">
                  <p class="text-xs text-inkSoft italic">{item.description}</p>
                </div>

                <!-- Existing Comments -->
                {#if item.comments && item.comments.length > 0}
                  <div class="space-y-3 mb-4">
                    {#each item.comments as comment}
                      <div class="bg-surface/50 rounded-xl p-3 relative group/comment">
                        {#if comment.user_id === user.id}
                          <button class="absolute top-2 right-2 p-1 text-inkSoft hover:text-coral opacity-0 group-hover/comment:opacity-100 transition-all" on:click|stopPropagation={() => handleDeleteComment(comment.id)} title="Delete Comment">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                          </button>
                        {/if}
                        <div class="flex items-center gap-2 mb-1.5 pr-6">
                          {#if comment.profile_pic_url}
                            <img src={comment.profile_pic_url} alt="Profile" class="w-5 h-5 rounded-full object-cover">
                          {/if}
                          <span class="text-xs font-bold text-ink">{comment.username}</span>
                          {#if comment.user_id === item.user_id}
                            <span class="text-[9px] bg-wave/20 text-wave px-1.5 py-0.5 rounded font-bold">SELLER</span>
                          {/if}
                        </div>
                        <p class="text-xs text-inkSoft pl-7">{@html formatMentions(comment.content)}</p>
                      </div>
                    {/each}
                  </div>
                {:else}
                  <p class="text-[11px] text-inkSoft italic mb-4">No questions asked yet.</p>
                {/if}
                
                <!-- Reply Input -->
                {#if !isSold}
                  <div class="flex gap-2 relative">
                    <input type="text" value={expandedItem === item.id ? replyContent : ''} on:input={(e) => handleTextInput(e, item.id)} class="input-field py-1.5 text-xs w-full bg-surfaceDeep" placeholder="Ask about this item..." on:keydown={(e) => e.key === 'Enter' && handlePostReply(item.id)}/>
                    <button class="px-3 py-1.5 bg-wave text-white rounded-lg text-xs font-bold hover:bg-deep transition-colors shrink-0 disabled:opacity-50" on:click={() => handlePostReply(item.id)} disabled={postingReply}>
                      Send
                    </button>

                    {#if showMentionSuggestions && activeMentionPostId === item.id}
                      <ul class="absolute bottom-full mb-2 z-50 w-[80%] bg-surface border border-black/10 rounded-xl max-h-48 overflow-y-auto shadow-glass">
                        {#each mentionSuggestions as mu}
                          <li>
                            <button class="w-full flex items-center gap-3 px-4 py-3 text-sm text-ink hover:bg-surfaceDeep transition-colors border-b border-black/5" on:click={() => selectMention(mu)}>
                              {#if mu.profile_pic_url}
                                <img src={mu.profile_pic_url} alt="Profile" class="w-8 h-8 rounded-full object-cover">
                              {:else}
                                <div class="w-8 h-8 rounded-full bg-wave text-white flex items-center justify-center font-bold">{getInitial(mu.username)}</div>
                              {/if}
                              {mu.username}
                            </button>
                          </li>
                        {/each}
                      </ul>
                    {/if}
                  </div>
                {/if}
              </div>
            {/if}
          </div>

        {:else}
          <!-- Discussions Layout -->
          <!-- svelte-ignore a11y-click-events-have-key-events -->
          <!-- svelte-ignore a11y-no-static-element-interactions -->
          <div transition:slide class="bg-white rounded-[24px] p-6 border-l-[6px] border-l-wave shadow-sm border border-black/5 hover:border-black/10 transition-colors cursor-pointer" on:click={() => expandedItem = expandedItem === item.id ? null : item.id}>
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full overflow-hidden bg-surfaceDeep flex items-center justify-center">
                  {#if item.profile_pic_url}
                    <img src={item.profile_pic_url} alt={item.username} class="w-full h-full object-cover"/>
                  {:else}
                    <span class="text-ink font-bold text-xs">{getInitial(item.username)}</span>
                  {/if}
                </div>
                <div>
                  <div class="font-bold text-ink text-sm leading-none">{item.username}</div>
                  <div class="text-[10px] text-inkSoft font-medium mt-1">{new Date(item.created_at || Date.now()).toLocaleDateString()}</div>
                </div>
              </div>
              
              {#if item.user_id === user.id}
                <button class="p-1.5 text-inkSoft hover:text-coral transition-colors" on:click|stopPropagation={() => handleDeleteItem(item.id)} title="Delete Discussion">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                </button>
              {/if}
            </div>
            <h3 class="text-xl font-display font-bold text-ink mb-2">{item.title}</h3>
            <p class="text-inkSoft text-sm leading-relaxed whitespace-pre-wrap">{item.content}</p>
            
            <div class="mt-4 pt-4 border-t border-black/5 flex items-center gap-4 text-xs font-bold text-inkSoft">
              <div class="flex items-center gap-1.5 group hover:text-wave transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>
                {item.comments ? item.comments.length : 0} Replies
              </div>
            </div>

            <!-- Accordion Comments Section -->
            {#if expandedItem === item.id}
              <div class="mt-4 pt-4 border-t border-black/5 space-y-4" transition:slide|local>
                <!-- Existing Comments -->
                {#if item.comments && item.comments.length > 0}
                  <div class="space-y-4 mb-4">
                    {#each item.comments as comment}
                      <div class="bg-surface/50 rounded-2xl p-4 relative group/comment">
                        {#if comment.user_id === user.id}
                          <button class="absolute top-3 right-3 p-1 text-inkSoft hover:text-coral opacity-0 group-hover/comment:opacity-100 transition-all" on:click|stopPropagation={() => handleDeleteComment(comment.id)} title="Delete Comment">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                          </button>
                        {/if}
                        <div class="flex items-center gap-2 mb-2 pr-6">
                          {#if comment.profile_pic_url}
                            <img src={comment.profile_pic_url} alt="Profile" class="w-5 h-5 rounded-full object-cover">
                          {:else}
                            <div class="w-5 h-5 rounded-full overflow-hidden bg-wave/20 flex items-center justify-center text-[9px] font-bold text-wave">
                              {getInitial(comment.username)}
                            </div>
                          {/if}
                          <span class="text-xs font-bold text-ink">{comment.username}</span>
                          <span class="text-[10px] text-inkSoft">{new Date(comment.created_at).toLocaleDateString()}</span>
                        </div>
                        <p class="text-sm text-inkSoft pl-7">{@html formatMentions(comment.content)}</p>
                      </div>
                    {/each}
                  </div>
                {/if}
                
                <!-- Reply Input -->
                <div class="flex gap-2 relative" on:click|stopPropagation>
                  <input type="text" value={expandedItem === item.id ? replyContent : ''} on:input={(e) => handleTextInput(e, item.id)} class="input-field py-2 text-sm w-full bg-surfaceDeep" placeholder="Write a reply..." on:keydown={(e) => e.key === 'Enter' && handlePostReply(item.id)}/>
                  <button class="px-4 py-2 bg-wave text-white rounded-xl text-sm font-bold hover:bg-deep transition-colors shrink-0 disabled:opacity-50" on:click={() => handlePostReply(item.id)} disabled={postingReply}>
                    Reply
                  </button>

                  {#if showMentionSuggestions && activeMentionPostId === item.id}
                    <ul class="absolute bottom-full mb-2 z-50 w-[80%] bg-surface border border-black/10 rounded-xl max-h-48 overflow-y-auto shadow-glass">
                      {#each mentionSuggestions as mu}
                        <li>
                          <button class="w-full flex items-center gap-3 px-4 py-3 text-sm text-ink hover:bg-surfaceDeep transition-colors border-b border-black/5" on:click={() => selectMention(mu)}>
                            {#if mu.profile_pic_url}
                              <img src={mu.profile_pic_url} alt="Profile" class="w-8 h-8 rounded-full object-cover">
                            {:else}
                              <div class="w-8 h-8 rounded-full bg-wave text-white flex items-center justify-center font-bold">{getInitial(mu.username)}</div>
                            {/if}
                            {mu.username}
                          </button>
                        </li>
                      {/each}
                    </ul>
                  {/if}
                </div>
              </div>
            {/if}
          </div>
        {/if}
      {/each}
    {/if}
  </div>

  <!-- Floating Action Button -->
  <button 
    class="fixed bottom-8 right-8 w-14 h-14 bg-wave text-white rounded-full shadow-xl flex items-center justify-center hover:scale-105 hover:bg-deep transition-all z-40 group"
    on:click={openModal}
  >
    <svg class="w-6 h-6 transition-transform group-hover:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
  </button>

  <!-- Modal Overlay -->
  {#if showModal}
    <div 
      class="fixed inset-0 bg-deep/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      transition:fade={{ duration: 150 }}
    >
      <!-- Modal Content -->
      <div 
        class="bg-white w-full max-w-lg rounded-[24px] shadow-2xl flex flex-col max-h-[90vh]"
        transition:slide={{ duration: 250, axis: 'y' }}
      >
        <div class="flex justify-between items-center p-6 border-b border-black/5 shrink-0">
          <h2 class="text-xl font-bold font-display text-ink">
            {#if activeTab === 'market'} Post to Marketplace
            {:else if activeTab === 'meetups'} Organize a Meetup
            {:else} Start a Discussion{/if}
          </h2>
          <button on:click={closeModal} class="text-inkSoft hover:text-coral transition-colors">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </button>
        </div>
        
        <div class="p-6 space-y-4 overflow-y-auto">
          <!-- Shared/Dynamic Inputs -->
          <div class="space-y-1">
            <label class="text-xs font-bold text-inkSoft uppercase tracking-wider">
              {#if activeTab === 'market'}Item Name{:else if activeTab === 'meetups'}Meetup Title{:else}Topic Title{/if}
            </label>
            <input type="text" bind:value={title} class="input-field py-3 text-sm w-full font-bold bg-surfaceDeep" placeholder="Give it a catchy title..." />
          </div>

          <!-- Market Specific -->
          {#if activeTab === 'market'}
            <!-- Real Photo Upload UI -->
            <input type="file" accept="image/*" bind:this={fileInput} on:change={handleFileSelect} class="hidden" />
            
            <!-- svelte-ignore a11y-click-events-have-key-events -->
            <!-- svelte-ignore a11y-no-static-element-interactions -->
            <div 
              class="w-full h-40 border-2 border-dashed rounded-xl flex flex-col items-center justify-center cursor-pointer transition-colors relative overflow-hidden {imagePreviewUrl ? 'border-wave/0 bg-surfaceDeep' : 'border-wave/40 bg-wave/5 text-wave hover:bg-wave/10'}"
              on:click={() => fileInput.click()}
            >
              {#if imagePreviewUrl}
                <img src={imagePreviewUrl} alt="Preview" class="w-full h-full object-cover" />
                <div class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                  <span class="text-white font-bold text-sm">Change Photo</span>
                </div>
              {:else}
                <svg class="w-8 h-8 mb-2 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                <span class="text-sm font-bold">Tap to add photo</span>
              {/if}
            </div>

            <div class="flex gap-4">
              <div class="space-y-1 w-1/2">
                <label class="text-xs font-bold text-inkSoft uppercase tracking-wider">Price (IDR)</label>
                <div class="relative">
                  <span class="absolute left-3 top-3 text-inkSoft font-bold text-sm">Rp</span>
                  <input type="number" bind:value={price} class="input-field py-3 pl-10 w-full bg-surfaceDeep font-bold text-sm" placeholder="4.500.000" />
                </div>
              </div>
              <div class="space-y-1 w-1/2">
                <label class="text-xs font-bold text-inkSoft uppercase tracking-wider">Condition</label>
                <select bind:value={condition} class="input-field py-3 w-full bg-surfaceDeep font-medium text-sm">
                  <option>New</option>
                  <option>Like new</option>
                  <option>Used - Good</option>
                  <option>Used - Fair</option>
                </select>
              </div>
            </div>
            
            <div class="space-y-1 relative">
              <label class="text-xs font-bold text-inkSoft uppercase tracking-wider">Location</label>
              <input type="text" value={marketLocation} on:input={(e) => handleLocationInput(e, 'market')} on:focus={() => { activeLocationField = 'market'; if(spotSuggestions.length) showSuggestions = true; }} class="input-field py-3 text-sm w-full bg-surfaceDeep" placeholder="e.g., Canggu, Bali" />
              {#if showSuggestions && activeLocationField === 'market'}
                <ul class="absolute z-50 w-full bg-white border border-black/10 rounded-xl mt-1 max-h-48 overflow-y-auto shadow-xl">
                  {#each spotSuggestions as spot}
                    <li>
                      <button class="w-full text-left px-4 py-2 text-sm text-ink hover:bg-surfaceDeep transition-colors" on:click={() => selectSpot(spot)}>
                        <span class="block font-semibold">📍 {spot.name}</span>
                        <span class="block text-xs text-inkSoft pl-5">{spot.region}</span>
                      </button>
                    </li>
                  {/each}
                </ul>
              {/if}
            </div>
          {/if}

          <!-- Meetup Specific -->
          {#if activeTab === 'meetups'}
            <div class="space-y-1 relative">
              <label class="text-xs font-bold text-inkSoft uppercase tracking-wider">Location / Meeting Point</label>
              <input type="text" value={meetupLocation} on:input={(e) => handleLocationInput(e, 'meetups')} on:focus={() => { activeLocationField = 'meetups'; if(spotSuggestions.length) showSuggestions = true; }} class="input-field py-3 text-sm w-full bg-surfaceDeep" placeholder="e.g., Batu Bolong Beach Warung" />
              {#if showSuggestions && activeLocationField === 'meetups'}
                <ul class="absolute z-50 w-full bg-white border border-black/10 rounded-xl mt-1 max-h-48 overflow-y-auto shadow-xl">
                  {#each spotSuggestions as spot}
                    <li>
                      <button class="w-full text-left px-4 py-2 text-sm text-ink hover:bg-surfaceDeep transition-colors" on:click={() => selectSpot(spot)}>
                        <span class="block font-semibold">📍 {spot.name}</span>
                        <span class="block text-xs text-inkSoft pl-5">{spot.region}</span>
                      </button>
                    </li>
                  {/each}
                </ul>
              {/if}
            </div>
            <div class="flex gap-4">
              <div class="space-y-1 w-1/2">
                <label class="text-xs font-bold text-inkSoft uppercase tracking-wider">Date</label>
                <input type="date" bind:value={meetupDate} class="input-field py-3 text-sm w-full bg-surfaceDeep" />
              </div>
              <div class="space-y-1 w-1/2">
                <label class="text-xs font-bold text-inkSoft uppercase tracking-wider">Time</label>
                <input type="time" bind:value={meetupTime} class="input-field py-3 text-sm w-full bg-surfaceDeep" />
              </div>
            </div>
            <div class="space-y-1">
              <label class="text-xs font-bold text-inkSoft uppercase tracking-wider">Target Skill Level</label>
              <select bind:value={meetupSkill} class="input-field py-3 w-full bg-surfaceDeep font-medium text-sm">
                <option>All Levels</option>
                <option>Beginner Friendly</option>
                <option>Intermediate/Advanced</option>
              </select>
            </div>
          {/if}

          <div class="space-y-1">
            <label class="text-xs font-bold text-inkSoft uppercase tracking-wider">
              {#if activeTab === 'market'}Description{:else if activeTab === 'meetups'}Event Details{:else}Content{/if}
            </label>
            <textarea bind:value={content} rows="4" class="input-field py-3 w-full bg-surfaceDeep text-sm resize-y" placeholder="Add some details..."></textarea>
          </div>
        </div>
        
        <div class="p-6 border-t border-black/5 bg-surface shrink-0 rounded-b-[24px]">
          <button 
            class="w-full py-3.5 bg-wave text-white rounded-xl text-sm font-bold shadow-md hover:bg-deep transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed" 
            on:click={handlePost} 
            disabled={loading}
          >
            {#if loading}
              <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              Processing...
            {:else}
              {#if activeTab === 'market'}List Item{:else if activeTab === 'meetups'}Create Meetup{:else}Post Discussion{/if}
            {/if}
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>
