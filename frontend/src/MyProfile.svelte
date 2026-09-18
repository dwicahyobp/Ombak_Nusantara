<script>
  export let user;
  
  let profile = { bio: '', skill_level: user.skill_level };
  let loading = false;
  
  async function loadProfile() {
    try {
      const res = await fetch(`/api/surf/users/${user.id}/profile`);
      if (res.ok) {
        const data = await res.json();
        profile.bio = data.bio || '';
        profile.skill_level = data.skill_level || user.skill_level;
        profile.profile_pic_url = data.profile_pic_url || user.profile_pic_url || null;
      }
    } catch (e) {
      console.error(e);
    }
  }
  
  import { onMount, createEventDispatcher } from 'svelte';
  import { addToast } from './stores/toast.js';
  const dispatch = createEventDispatcher();
  onMount(loadProfile);
  
  async function handleProfilePicUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    loading = true;
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      
      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();
      profile.profile_pic_url = data.url;
      addToast('Image uploaded. Click Save to apply.', 'success');
    } catch (e) {
      addToast(e.message, 'error');
    } finally {
      loading = false;
    }
  }
  
  async function updateProfile() {
    loading = true;
    try {
      // Update Bio
      const resBio = await fetch(`/api/surf/users/${user.id}/bio`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bio: profile.bio })
      });
      
      // Update Skill Level
      const resSkill = await fetch(`/api/surf/users/${user.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill_level: profile.skill_level })
      });
      
      // Update Profile Pic
      let resPic = { ok: true };
      if (profile.profile_pic_url) {
        resPic = await fetch(`/api/surf/users/${user.id}/profile_pic`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ profile_pic_url: profile.profile_pic_url })
        });
      }

      if (resBio.ok && resSkill.ok && resPic.ok) {
        // Update local user object
        user.skill_level = profile.skill_level;
        if (profile.profile_pic_url) user.profile_pic_url = profile.profile_pic_url;
        dispatch('userUpdated', user);
        
        // Update user object in local storage
        const storedUser = JSON.parse(localStorage.getItem('user'));
        if (storedUser) {
          storedUser.skill_level = profile.skill_level;
          if (profile.profile_pic_url) storedUser.profile_pic_url = profile.profile_pic_url;
          localStorage.setItem('user', JSON.stringify(storedUser));
        }
        
        addToast('Profile updated successfully!', 'success');
      } else {
        throw new Error('Failed to update profile');
      }
    } catch (e) {
      addToast(e.message, 'error');
    } finally {
      loading = false;
    }
  }
</script>

<div class="glass-card max-w-2xl mx-auto space-y-6 shadow-sm">
  <div class="flex items-center gap-4 mb-6 border-b border-black/5 pb-6">
    <div 
      class="relative w-20 h-20 rounded-full bg-wave flex items-center justify-center text-white text-3xl font-bold cursor-pointer group overflow-hidden border-2 border-transparent hover:border-deep transition-all shadow-md"
      on:click={() => document.getElementById('profilePicInput').click()}
      on:keydown={(e) => e.key === 'Enter' && document.getElementById('profilePicInput').click()}
      role="button"
      tabindex="0"
    >
      {#if profile.profile_pic_url || user.profile_pic_url}
        <img src={profile.profile_pic_url || user.profile_pic_url} alt="Profile" class="w-full h-full object-cover" />
      {:else}
        {user.username.charAt(0).toUpperCase()}
      {/if}
      
      <div class="absolute inset-0 bg-black/40 hidden group-hover:flex items-center justify-center transition-all backdrop-blur-sm">
        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
      </div>
    </div>
    
    <input 
      type="file" 
      id="profilePicInput" 
      accept="image/*" 
      class="hidden" 
      on:change={handleProfilePicUpload} 
    />
    
    <div>
      <h2 class="text-2xl font-bold text-ink">{user.username}</h2>
      <p class="text-safe font-semibold">Skill Level: {user.skill_level}</p>
      <p class="text-xs text-inkSoft mt-1">Click avatar to change picture</p>
    </div>
  </div>

  <div class="space-y-4">
    <div class="space-y-2">
      <h3 class="text-xl font-semibold text-ink">Skill Level</h3>
      <select bind:value={profile.skill_level} class="input-field">
        <option value="Beginner">Beginner</option>
        <option value="Intermediate">Intermediate</option>
        <option value="Advanced">Advanced</option>
        <option value="Expert">Expert</option>
      </select>
    </div>

    <div class="space-y-2">
      <h3 class="text-xl font-semibold text-ink">About Me</h3>
      <textarea 
        bind:value={profile.bio} 
        class="input-field h-32" 
        placeholder="Tell us about yourself and your surf experience..."
      ></textarea>
    </div>
    
    <button class="btn-primary" on:click={updateProfile} disabled={loading}>
      {loading ? 'Saving...' : 'Update Profile'}
    </button>
  </div>
</div>
