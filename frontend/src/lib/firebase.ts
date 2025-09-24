
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "AIzaSyD0LIf31ekvYTPU7zNz4NnUshcrcI9q0KM",
  authDomain: "cliplink-78521.firebaseapp.com",
  projectId: "cliplink-78521",
  storageBucket: "cliplink-78521.appspot.com",
  messagingSenderId: "882907930174",
  appId: "1:882907930174:web:2fea6639433d5b01103b6f",
  measurementId: "G-XYRWRBJYP6"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
