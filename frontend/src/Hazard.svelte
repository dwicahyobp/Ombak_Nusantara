<script>
  import { onMount } from 'svelte';
  import { fade, slide } from 'svelte/transition';
  import { addToast } from './stores/toast.js';
  import { INDO_SURF_SPOTS } from './surfSpots.js';

  export let user;
  
  let reports = [];
  let loading = false;
  
  // Form fields
  let hazardType = 'Shark Sighting';
  let location = '';
  let locationLat = null;
  let locationLng = null;
  let description = '';
  let severity = 3;
  let fileInput;
  let selectedFile = null;
  let imagePreviewUrl = null;
  let uploadLoading = false;
  
  const HAZARD_TYPES = ['Shark Sighting', 'Jellyfish Swarm', 'Rip Current', 'Water Pollution', 'Reef Damage', 'Other'];
  
  // Predictive Location Search
  let spotSuggestions = [];
  let showSuggestions = false;
  let searchTimeout = null;

  // Mention System
  let mentionSuggestions = [];
  let showMentionSuggestions = false;
  let mentionSearchTimeout = null;
  let activeMentionType = null;
  let activeMentionPostId = null;

  // Comments
  let expandedItem = null;
  let commentInputs = {};
  
  async function loadReports() {
    loading = true;
    try {
      const res = await fetch('/api/social/hazards');
      if (res.ok) {
        reports = await res.json();
      }
    } catch (e) {
      console.error(e);
    } finally {
      loading = false;
    }
  }
  
  onMount(loadReports);

  function formatMentions(text) {
    if (!text) return '';
    return text.replace(/@([a-zA-Z0-9_]+)/g, '<span class="text-wave font-bold hover:underline cursor-pointer">@$1</span>');
  }

  async function handleTextInput(e, type, postId = null) {
    const val = e.target.value;
    const cursorPosition = e.target.selectionStart;
    
    if (type === 'description') description = val;
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
    let currentText = '';
    if (activeMentionType === 'description') currentText = description;
    else if (activeMentionType === 'comment') currentText = commentInputs[activeMentionPostId];

    const words = currentText.split(/[\s\n]+/);
    words.pop(); // remove partial mention
    words.push(`@${userObj.username} `);
    const newText = words.join(' ');

    if (activeMentionType === 'description') description = newText;
    else if (activeMentionType === 'comment') commentInputs[activeMentionPostId] = newText;

    showMentionSuggestions = false;
  }

  function handleLocationInput(e) {
    location = e.target.value;
    locationLat = null; // reset coords when user types
    locationLng = null;
    if (location.length < 2) {
      spotSuggestions = [];
      showSuggestions = false;
      return;
    }
    
    if (searchTimeout) clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
      let localMatches = INDO_SURF_SPOTS.filter(spot => 
        spot.name.toLowerCase().includes(location.toLowerCase()) || 
        spot.region.toLowerCase().includes(location.toLowerCase())
      );

      if (localMatches.length > 0) {
        spotSuggestions = localMatches.slice(0, 5);
        showSuggestions = true;
      } else {
        try {
          const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(location)}&format=json&limit=5`);
          if (res.ok) {
            const data = await res.json();
            spotSuggestions = data.map(d => ({
              name: d.name || d.display_name.split(',')[0],
              region: d.display_name.split(',').slice(-2).join(', ').trim(),
              lat: parseFloat(d.lat),
              lng: parseFloat(d.lon)
            }));
            showSuggestions = true;
          }
        } catch (err) {}
      }
    }, 500);
  }

  function selectLocation(spot) {
    location = spot.region ? `${spot.name}, ${spot.region}` : spot.name;
    locationLat = spot.lat || null;
    locationLng = spot.lng || null;
    showSuggestions = false;
  }

  function handleWindowClick(e) {
    if (!e.target.closest('.location-container')) showSuggestions = false;
    if (!e.target.closest('.mention-container')) showMentionSuggestions = false;
  }
  
  function triggerFileInput() {
    fileInput.click();
  }

  async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 20 * 1024 * 1024) {
      addToast('File is too large. Max 20MB', 'error');
      return;
    }

    selectedFile = file;
    uploadLoading = true;

    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (event) => {
        imagePreviewUrl = event.target.result;
      };
      reader.readAsDataURL(file);
    } else if (file.type.startsWith('video/')) {
      imagePreviewUrl = null; // show a video icon or something instead
    }

    uploadLoading = false;
  }
  
  async function handleReport() {
    if (!location.trim() || !description.trim()) return addToast('Please fill all fields', 'warning');
    
    loading = true;
    try {
      let mediaUrl = null;
      if (selectedFile) {
        const formData = new FormData();
        formData.append('file', selectedFile);
        const uploadRes = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        });
        if (uploadRes.ok) {
          const uploadData = await uploadRes.json();
          mediaUrl = uploadData.url;
        }
      }

      const payload = {
        hazard_type: hazardType,
        location,
        latitude: locationLat,
        longitude: locationLng,
        description,
        severity,
        reporter_id: user.id,
        media_url: mediaUrl
      };
      
      const res = await fetch('/api/social/hazards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) throw new Error('Failed to submit report');
      
      addToast('Hazard reported successfully', 'success');
      location = '';
      locationLat = null;
      locationLng = null;
      description = '';
      severity = 3;
      hazardType = 'Shark Sighting';
      selectedFile = null;
      imagePreviewUrl = null;
      loadReports();
    } catch (e) {
      addToast(e.message, 'error');
    } finally {
      loading = false;
    }
  }

  async function handleDeleteReport(id) {
    if (!confirm('Are you sure you want to delete this report?')) return;
    try {
      const res = await fetch(`/api/social/hazards/${id}?user_id=${user.id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete report');
      addToast('Report deleted', 'success');
      loadReports();
    } catch (e) {
      addToast(e.message, 'error');
    }
  }

  async function handleComment(reportId) {
    const text = commentInputs[reportId];
    if (!text?.trim()) return;

    try {
      const payload = {
        user_id: user.id,
        content: text
      };
      const res = await fetch(`/api/social/hazards/${reportId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) throw new Error('Failed to post comment');
      commentInputs[reportId] = '';
      addToast('Comment posted', 'success');
      loadReports();
    } catch (e) {
      addToast(e.message, 'error');
    }
  }

  async function handleDeleteComment(commentId) {
    if (!confirm('Are you sure you want to delete this comment?')) return;
    try {
      const res = await fetch(`/api/social/hazards/comments/${commentId}?user_id=${user.id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete comment');
      addToast('Comment deleted', 'success');
      loadReports();
    } catch (e) {
      addToast(e.message, 'error');
    }
  }
</script>

<svelte:window on:click={handleWindowClick} />

<div class="space-y-6 max-w-4xl mx-auto pb-20">
  <div class="bg-coral/10 border border-coral/20 rounded-[24px] p-6 mb-6 text-coral shadow-sm">
    <h2 class="text-xl font-bold mb-1 flex items-center gap-2">
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
      Local Hazard Reports
    </h2>
    <p class="text-sm font-medium opacity-90">Help keep the community safe by reporting marine life, currents, or pollution.</p>
  </div>

  <!-- Create Report Form -->
  <div class="bg-white/50 rounded-[24px] p-6 space-y-4 shadow-sm border border-black/5 animate-fade-down relative">
    <div class="flex flex-col md:flex-row gap-4">
      <div class="space-y-1 md:w-1/3">
        <label class="text-xs font-bold text-inkSoft uppercase tracking-wider">Hazard Type</label>
        <select bind:value={hazardType} class="input-field py-3 w-full bg-white shadow-sm border-black/5 font-medium text-sm">
          {#each HAZARD_TYPES as type}
            <option value={type}>{type}</option>
          {/each}
        </select>
      </div>
      <div class="space-y-1 md:w-2/3 location-container relative">
        <label class="text-xs font-bold text-inkSoft uppercase tracking-wider">Location</label>
        <input 
          type="text" 
          value={location} 
          on:input={handleLocationInput}
          on:focus={() => { if (spotSuggestions.length) showSuggestions = true; }}
          class="input-field py-3 w-full bg-white shadow-sm border-black/5 text-sm" 
          placeholder="e.g. Uluwatu - 3rd Peak" 
        />
        {#if showSuggestions}
          <ul class="absolute top-full mt-1 z-50 w-full bg-white border border-black/10 rounded-xl max-h-48 overflow-y-auto shadow-glass">
            {#each spotSuggestions as spot}
              <li>
                <button class="w-full flex flex-col px-4 py-2 text-left hover:bg-surfaceDeep transition-colors border-b border-black/5" on:click={() => selectLocation(spot)}>
                  <span class="text-sm font-bold text-ink">{spot.name}</span>
                  <span class="text-[10px] font-medium text-inkSoft">{spot.region}</span>
                </button>
              </li>
            {/each}
          </ul>
        {/if}
      </div>
    </div>
    
    <div class="space-y-1 mention-container relative">
      <label class="text-xs font-bold text-inkSoft uppercase tracking-wider">Description</label>
      <textarea 
        value={description} 
        on:input={(e) => handleTextInput(e, 'description')}
        rows="3" 
        class="input-field py-3 resize-y w-full bg-white shadow-sm border-black/5 text-sm" 
        placeholder="Describe the hazard in detail... @mention someone"
      ></textarea>
      
      {#if showMentionSuggestions && activeMentionType === 'description'}
        <ul class="absolute bottom-full mb-1 z-50 w-64 bg-white border border-black/10 rounded-xl max-h-48 overflow-y-auto shadow-glass">
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
    
    <!-- Media Preview -->
    {#if imagePreviewUrl || selectedFile}
      <div class="relative w-fit">
        {#if imagePreviewUrl}
          <img src={imagePreviewUrl} alt="Preview" class="h-32 object-cover rounded-xl border border-black/10 shadow-sm" />
        {:else if selectedFile}
          <div class="h-32 w-32 flex items-center justify-center bg-surface border border-black/10 rounded-xl shadow-sm text-inkSoft">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
          </div>
        {/if}
        <button class="absolute -top-2 -right-2 bg-coral text-white w-6 h-6 rounded-full flex items-center justify-center hover:scale-110 transition-transform shadow-md" on:click={() => {selectedFile = null; imagePreviewUrl = null;}}>
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>
    {/if}

    <div class="flex items-center gap-4 bg-surfaceDeep p-4 rounded-xl border border-black/5">
      <span class="font-bold text-ink text-sm whitespace-nowrap">Severity Level: {severity}/5</span>
      <input 
        type="range" 
        min="1" 
        max="5" 
        bind:value={severity} 
        class="w-full accent-coral cursor-pointer" 
      />
    </div>
    
    <div class="flex justify-between items-center pt-2">
      <input type="file" bind:this={fileInput} on:change={handleFileUpload} accept="image/*,video/*" class="hidden">
      <button class="flex items-center gap-2 text-inkSoft hover:text-wave transition-colors font-bold text-sm" on:click={triggerFileInput}>
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
        Add Photo/Video
      </button>

      <button class="bg-coral text-white font-bold py-2.5 px-6 rounded-xl shadow-sm hover:shadow-md hover:bg-red-500 active:scale-95 transition-all text-sm" on:click={handleReport} disabled={loading || uploadLoading}>
        {loading || uploadLoading ? 'Submitting...' : 'Submit Report'}
      </button>
    </div>
  </div>

  <!-- Reports List -->
  <div class="space-y-4 pt-4">
    <h3 class="text-xl font-display font-bold text-ink mb-4">Recent Reports</h3>
    {#if loading && reports.length === 0}
      <div class="flex justify-center py-10">
        <div class="w-8 h-8 border-4 border-coral border-t-transparent rounded-full animate-spin"></div>
      </div>
    {:else if reports.length === 0}
      <div class="bg-white/50 rounded-[24px] text-center py-12 border-dashed border-2 border-black/10">
        <div class="text-4xl mb-4 opacity-50">🌊</div>
        <p class="text-safe font-bold">All clear!</p>
        <p class="text-inkSoft text-sm">No recent hazards reported in the network.</p>
      </div>
    {:else}
      {#each reports as report (report.id)}
        <div transition:slide class="bg-white rounded-[24px] p-6 border-l-[6px] {report.severity >= 4 ? 'border-l-coral' : report.severity == 3 ? 'border-l-amber-500' : 'border-l-safe'} shadow-sm border border-black/5 hover:border-black/10 transition-colors">
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full overflow-hidden bg-surfaceDeep flex items-center justify-center">
                {#if report.profile_pic_url}
                  <img src={report.profile_pic_url} alt={report.username} class="w-full h-full object-cover"/>
                {:else}
                  <span class="text-ink font-bold text-sm">{report.username ? report.username.charAt(0).toUpperCase() : '?'}</span>
                {/if}
              </div>
              <div>
                <div class="font-bold text-ink text-sm leading-none">{report.username || `User ${report.reporter_id}`}</div>
                <div class="text-[10px] text-inkSoft font-medium mt-1">{new Date(report.created_at).toLocaleString()}</div>
              </div>
            </div>
            
            <div class="flex items-center gap-2">
              <span class="inline-flex px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider bg-surfaceDeep text-ink uppercase">
                {report.hazard_type}
              </span>
              {#if report.severity >= 4}
                <span class="inline-flex px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider bg-coral/10 text-coral uppercase animate-pulse">
                  Critical
                </span>
              {/if}
              {#if report.reporter_id === user.id}
                <button class="p-1 text-inkSoft hover:text-coral transition-colors ml-2" on:click={() => handleDeleteReport(report.id)}>
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                </button>
              {/if}
            </div>
          </div>
          
          <h3 class="text-lg font-bold text-ink mb-2 flex items-center gap-1.5">
            <svg class="w-4 h-4 text-inkSoft" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
            {report.location}
          </h3>
          <p class="text-inkSoft text-sm leading-relaxed whitespace-pre-wrap mb-4">{@html formatMentions(report.description)}</p>
          
          {#if report.media_url}
            <div class="my-4 max-w-sm rounded-xl overflow-hidden border border-black/5 shadow-sm">
              {#if report.media_url.endsWith('.mp4') || report.media_url.endsWith('.webm')}
                <video src={report.media_url} controls class="w-full h-auto max-h-64 object-cover"></video>
              {:else}
                <img src={report.media_url} alt="Hazard" class="w-full h-auto max-h-64 object-cover">
              {/if}
            </div>
          {/if}
          
          <div class="pt-4 border-t border-black/5 flex items-center justify-between">
            <span class="text-xs font-bold {report.severity >= 4 ? 'text-coral' : report.severity == 3 ? 'text-amber-500' : 'text-safe'}">
              Severity: {report.severity}/5
            </span>

            <button class="text-xs font-bold text-inkSoft hover:text-wave flex items-center gap-1 transition-colors" on:click={() => expandedItem = expandedItem === report.id ? null : report.id}>
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
              {report.comments ? report.comments.length : 0} Comments
            </button>
          </div>

          <!-- Comments Section -->
          {#if expandedItem === report.id}
            <div class="mt-4 pt-4 border-t border-black/5 space-y-4" transition:slide>
              {#if report.comments && report.comments.length > 0}
                <div class="space-y-3">
                  {#each report.comments as comment}
                    <div class="flex gap-3 group/comment relative">
                      <div class="w-6 h-6 rounded-full overflow-hidden bg-surfaceDeep flex-shrink-0">
                        {#if comment.profile_pic_url}
                          <img src={comment.profile_pic_url} alt="Profile" class="w-full h-full object-cover">
                        {:else}
                          <div class="w-full h-full bg-wave text-white flex items-center justify-center text-[10px] font-bold">
                            {comment.username.charAt(0).toUpperCase()}
                          </div>
                        {/if}
                      </div>
                      <div class="bg-surfaceDeep px-3 py-2 rounded-xl rounded-tl-none w-fit max-w-[85%] relative">
                        <div class="flex items-center gap-2 mb-0.5">
                          <span class="text-xs font-bold text-ink">{comment.username}</span>
                          <span class="text-[10px] text-inkSoft">{new Date(comment.created_at).toLocaleString()}</span>
                        </div>
                        <span class="text-xs text-ink whitespace-pre-wrap leading-relaxed">{@html formatMentions(comment.content)}</span>
                        
                        {#if comment.user_id === user.id}
                          <button class="absolute -right-8 top-2 text-inkSoft hover:text-coral opacity-0 group-hover/comment:opacity-100 transition-all" on:click={() => handleDeleteComment(comment.id)}>
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                          </button>
                        {/if}
                      </div>
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="text-center py-4 text-inkSoft text-xs font-medium">No comments yet. Be the first to discuss!</div>
              {/if}
              
              <!-- Add Comment Input -->
              <div class="flex gap-2 items-center mt-2 relative mention-container">
                <input 
                  type="text" 
                  value={commentInputs[report.id] || ''} 
                  on:input={(e) => handleTextInput(e, 'comment', report.id)}
                  on:keydown={(e) => { if (e.key === 'Enter') handleComment(report.id); }}
                  placeholder="Add a comment... @mention someone" 
                  class="input-field py-2 px-4 text-xs w-full bg-surfaceDeep"
                >
                <button class="bg-coral text-white p-2 rounded-xl shadow-sm hover:scale-105 active:scale-95 transition-transform" on:click={() => handleComment(report.id)}>
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                </button>

                {#if showMentionSuggestions && activeMentionType === 'comment' && activeMentionPostId === report.id}
                  <ul class="absolute bottom-full mb-1 z-50 w-full bg-white border border-black/10 rounded-xl max-h-48 overflow-y-auto shadow-glass">
                    {#each mentionSuggestions as mu}
                      <li>
                        <button class="w-full flex items-center gap-3 px-4 py-2 text-sm text-ink hover:bg-surfaceDeep transition-colors border-b border-black/5" on:click={() => selectMention(mu)}>
                          {#if mu.profile_pic_url}
                            <img src={mu.profile_pic_url} alt="Profile" class="w-6 h-6 rounded-full object-cover">
                          {:else}
                            <div class="w-6 h-6 rounded-full bg-wave text-white flex items-center justify-center font-bold text-xs">{mu.username.charAt(0).toUpperCase()}</div>
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
      {/each}
    {/if}
  </div>
</div>
