export interface AuthUser {
  id: number;
  username: string;
  is_active: boolean;
  is_admin: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface AuthCredentials {
  username: string;
  password: string;
}
