import type { Request, Response, NextFunction } from 'express';
import { auth } from '../config/firebaseConfig.js';

export const authenticate = async (req: Request, res: Response, next: NextFunction) => {
    const token = req.headers.authorization?.split(' ')[1];

    if (!token) {
        return res.status(401).json({ message: 'Authentication required' });
    }

    try {
        const decodedToken = await auth.verifyIdToken(token);
        (req as any).user = {
            userId: decodedToken.uid,
            email: decodedToken.email,
            role: decodedToken.role || 'CLIENT' // Custom claims if set
        };
        next();
    } catch (error) {
        console.error("Token verification failed:", error);
        return res.status(403).json({ message: 'Invalid token' });
    }
};
