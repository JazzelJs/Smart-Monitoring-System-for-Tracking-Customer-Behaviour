export const saveTokens = (access, refresh) => {
    localStorage.setItem('access', access);
    localStorage.setItem('refresh', refresh);
  };
  
  export const saveAccessToken = (access) => {
    localStorage.setItem('access', access);
  };
  
  export const getAccessToken = () => localStorage.getItem('access');
  export const getRefreshToken = () => localStorage.getItem('refresh');
  
  export const clearTokens = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
  };
  