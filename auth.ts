"use server";
import { cookies } from "next/headers";

export async function auth() {
    // Check if cookies exist
    const isCookies = cookies().has("user_data");

    if (!isCookies) {
        console.log("[auth] No cookies. Redirecting to login.");
        return null;
    }

    const cookies_user_data = cookies().get("user_data")?.value;

    if (!cookies_user_data) {
        console.log("[auth] No user data in cookies. Redirecting to login.");
        return null;
    }

    let user_data: UserData;
    try {
        user_data = JSON.parse(cookies_user_data);
    } catch (error) {
        console.error("Error parsing cookies_user_data in auth.ts:", error);
        // handle the error appropriately, e.g., by setting user_data to a default value
        user_data = {} as UserData;
    }
    console.log("[auth] user_data CALLED @auth");

    if (!user_data.access_token) {
        console.log("[auth] Expired Redirecting to login.");
        return null;
    }

    return user_data;
}

export async function signOut() {
    cookies().delete("user_data");
    console.log("[signOut] User data cookie deleted. Redirecting to login.");
}
